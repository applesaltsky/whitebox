## 1. what is whitebox

Whitebox is a simple Python project for creating personal blogs. It is built on Python FastAPI and controls the database using SQLite. The code for downloading and running it is as follows

```
git clone https://github.com/applesaltsky/whitebox
cd whitebox
pip install -r requirements.txt
python app.py
```

When you access 'http://0.0.0.0:8080', you will see a website like this. (This is my personal blog that I am currently running.)

[https://whitebox.social](https://whitebox.social)

## 2. config and admin panel

All configuration settings for this app are located in controller/config.py.
You can change some port, ip, category setting and etc.
When you login with admin previlage, you can access to admin panel for handling sqlite database with sql directly. All control, create, read, update, delete are allowed in that panel.

If you want to add one category, accecss admin panel, and run this sql.

```
INSERT CATEGORY_TABLE (
    CATEGORY_IDX,
    CATEGORY
) VALUES (
    4,
    NEW_CATEGORY_NAME
)
```

Then, one category will be created.
(All information for sqlite db are located in contoller/db_control_sql.py, and controller/db_control.py.)