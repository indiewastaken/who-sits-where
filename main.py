import threading
import requests
from bs4 import BeautifulSoup
import csv
import time

url = "https://dau-main-exams.hf.space/view_schedule/"

csrf_token_1 = "FtrAVoYZH2icq23HerNpB8CQXeGBe6wf7yuEvOYCGiAUGpxSyKXZfFkVhZN2jcSf"
csrf_token_2 = "r7WlDaKCJ53pZYAvKHIyfAbVy3tHq4TiTcZpdAKfIll7fl4G40S8T7T0SOA8vafi"

id_ranges_1 = [f"202301{str(i).zfill(3)}" for i in list(range(1, 194)) + list(range(195, 250))]
id_ranges_2 = [f"202301{str(i).zfill(3)}" for i in list(range(251, 288)) + list(range(401, 489))]

exam_date = "May 2, 2025"

lock = threading.Lock()

with open("exam_schedule_may2.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Student Name", "Student ID", "Exam Date", "Room Number", "Subject Name", "Subject Code", "Seat Number"])

def save_to_csv(row):
    with lock:
        with open("exam_schedule_may2.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)

def parse_response(html, student_id):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        print(f"[{student_id}] Skipped")
        return False
    rows = table.find("tbody").find_all("tr")
    count = 0
    for row in rows:
        cols = [td.text.strip() for td in row.find_all("td")]
        if exam_date in cols:
            save_to_csv(cols)
            count += 1
    if count:
        print(f"[{student_id}] Fetched")
    else:
        print(f"[{student_id}] Skipped")
    return True

def worker(ids, csrf_token):
    session = requests.Session()
    session.cookies.set("csrftoken", csrf_token, domain="dau-main-exams.hf.space")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": url
    }
    for student_id in ids:
        payload = {
            "csrfmiddlewaretoken": csrf_token,
            "student_id": student_id,
            "exam_date": "2025-05-02"
        }
        try:
            response = session.post(url, data=payload, headers=headers)
            if response.status_code == 200:
                parse_response(response.text, student_id)
            else:
                print(f"[{student_id}] Skipped (HTTP {response.status_code})")
            time.sleep(0.2)
        except Exception as e:
            print(f"[{student_id}] Skipped (Exception: {e})")

def run_threads(id_range, csrf_token):
    threads = []
    chunk_size = len(id_range) // 10
    for i in range(10):
        chunk = id_range[i*chunk_size:(i+1)*chunk_size] if i < 9 else id_range[i*chunk_size:]
        t = threading.Thread(target=worker, args=(chunk, csrf_token))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

t1 = threading.Thread(target=run_threads, args=(id_ranges_1, csrf_token_1))
t2 = threading.Thread(target=run_threads, args=(id_ranges_2, csrf_token_2))

t1.start()
t2.start()
t1.join()
t2.join()

print("Done! Data saved to exam_schedule.csv")