#!/usr/bin/env python3
import os
import time
import re
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Helper to parse a duration string such as "46s" or "4m 14s"
def parse_duration(duration_str):
    try:
        duration_str = duration_str.strip()
        minutes = 0
        seconds = 0
        if "m" in duration_str:
            parts = duration_str.split("m")
            minutes = int(parts[0].strip())
            seconds_part = parts[1].replace("s", "").strip()
            if seconds_part:
                seconds = int(seconds_part)
        elif duration_str.endswith("s"):
            seconds = int(duration_str.replace("s", "").strip())
        else:
            return 0
        total_minutes = minutes + (1 if seconds > 0 else 0)
        return total_minutes
    except Exception as e:
        print(f"Error parsing duration '{duration_str}': {e}")
        return 0

# Fallback function to extract a duration string from text using regex.
def extract_duration_from_text(text):
    match = re.search(r'(\d+\s*m\s*\d+\s*s|\d+\s*m\d+\s*s|\d+\s*s)', text, re.IGNORECASE)
    if match:
        return match.group(0)
    return None

# Use a persistent Chrome profile to retain credentials.
def linkedin_login():
    chrome_options = Options()
    profile_path = os.path.join(os.getcwd(), "selenium_profile")
    chrome_options.add_argument(f"user-data-dir={profile_path}")
    chrome_options.add_argument("--window-size=1200,800")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.linkedin.com/learning/")
    print("If you're not already logged in, please log in in the opened Selenium browser (complete any required 2FA).")
    input("Press Enter once you're logged in (and can see the LinkedIn Learning homepage)...")
    print("Continuing with the current session.")
    return driver

def scrape_course_lessons(driver, course_url):
    if not course_url.startswith("http"):
        course_url = "https://" + course_url
    driver.get(course_url)

    wait = WebDriverWait(driver, 30)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.classroom-toc-section__items")))
    except Exception:
        print("Course page did not load as expected or no lesson container found.")
        return []

    lesson_items = driver.find_elements(By.CSS_SELECTOR, "li.classroom-toc-item")
    print(f"Found {len(lesson_items)} lesson items.")
    lessons = []
    for li_item in lesson_items:
        try:
            lesson_link = li_item.find_element(By.CSS_SELECTOR, "a.classroom-toc-item__link")
            title_elem = lesson_link.find_element(By.CSS_SELECTOR, "div.classroom-toc-item__title")
            lesson_title = title_elem.text.strip()
            lesson_title_clean = lesson_title.replace("(Viewed)", "").replace("(In progress)", "").strip()

            estimated_minutes = 0
            duration_elem = None
            try:
                duration_elem = li_item.find_element(By.CSS_SELECTOR, "span.classroom-toc-item__duration")
            except Exception:
                try:
                    duration_elem = li_item.find_element(By.CSS_SELECTOR, "div.classroom-toc-item__duration")
                except Exception:
                    duration_elem = None

            if duration_elem:
                raw_duration = duration_elem.text.strip()
                lines = raw_duration.split("\n")
                candidate = lines[-1] if lines else raw_duration
                candidate = candidate.replace("video", "").strip()
                estimated_minutes = parse_duration(candidate)
            if estimated_minutes == 0:
                candidate = extract_duration_from_text(li_item.text)
                if candidate:
                    estimated_minutes = parse_duration(candidate)

            partial_url = lesson_link.get_attribute("href")
            if partial_url and not partial_url.startswith("http"):
                lesson_url = "https://www.linkedin.com/" + partial_url.lstrip("/")
            else:
                lesson_url = partial_url or course_url

            lessons.append({
                "title": lesson_title_clean,
                "url": lesson_url,
                "estimated_minutes": estimated_minutes
            })
            print(f"Found lesson: {lesson_title_clean} ({estimated_minutes} min)")
        except Exception as e:
            print(f"Skipping a lesson item due to error: {e}")
            continue
    return lessons

def find_or_create_project(project_name):
    applescript = f'''
    on findOrCreateProject(projName)
        tell application "OmniFocus"
            tell default document
                set foundProjects to every flattened project whose name is projName
                if (count of foundProjects) > 0 then
                    return first item of foundProjects
                else
                    make new project with properties {{name:projName}}
                    return first flattened project whose name is projName
                end if
            end tell
        end tell
    end findOrCreateProject

    findOrCreateProject("{project_name}")
    '''
    proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
    if proc.returncode != 0:
        print("Error in finding or creating project:")
        print(proc.stderr)
        return None
    return project_name

def create_task_in_omnifocus(project_name, task_title, note="", estimated_minutes=0):
    applescript = f'''
    tell application "OmniFocus"
        tell default document
            set theProject to first flattened project where name is "{project_name}"
            tell theProject
                make new task with properties {{name:"{task_title}", note:"{note}", estimated minutes:{estimated_minutes}}}
            end tell
        end tell
    end tell
    '''
    proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Error creating task: {task_title}")
        print(proc.stderr)
    else:
        print(f"Task '{task_title}' added to project '{project_name}' with estimated minutes {estimated_minutes}.")

def main():
    driver = linkedin_login()
    
    while True:
        course_url = input("Enter the LinkedIn Learning course URL (or enter N to exit): ").strip()
        if course_url.lower() == "n":
            break

        project_name = input("Enter the new OmniFocus project name: ").strip()
        
        lessons = scrape_course_lessons(driver, course_url)
        if not lessons:
            print("No lessons found on the specified page. Skipping this course.")
            continue
        print(f"Found {len(lessons)} lessons.")

        project_name = find_or_create_project(project_name)
        if project_name is None:
            print("Could not create or find the OmniFocus project. Skipping this course.")
            continue

        count = 1
        for lesson in lessons:
            task_title = f"{count} - {lesson['title']}"
            note = f"Lesson URL: {lesson['url']}"
            estimated_minutes = lesson.get("estimated_minutes", 0)
            create_task_in_omnifocus(project_name, task_title, note, estimated_minutes)
            time.sleep(0.5)
            count += 1
        print("All lessons have been added as tasks to OmniFocus for this course.\n")

    print("Exiting application.")
    driver.quit()

if __name__ == "__main__":
    main()