# 博客网站部署文档

> 服务器: `159.75.241.101` | 系统: Ubuntu 22.04 | 域名: 暂无（IP直连）

---

## 一、服务器配置

### 1. 安装软件

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv python3-dev nginx git
```

装了什么:
- `python3-pip` / `python3-venv` — Python 包管理和虚拟环境
- `python3-dev` — Python 头文件（编译 Pillow 需要）
- `nginx` — Web 服务器，监听 80 端口
- `git` — 代码版本管理

### 2. 安装 Python 依赖

```bash
cd /home/www/gallery
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

安装的包: `django==5.2.15` `pymysql` `Pillow` `gunicorn==26.0.0`

### 3. .env 环境变量

路径: `/home/www/gallery/.env`

```env
DJANGO_SECRET_KEY=<随机生成>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=159.75.241.101
```

---

## 二、项目文件列表

| 路径 | 说明 |
|---|---|
| `/home/www/gallery/blog/` | 博客应用代码 |
| `/home/www/gallery/blogproject/` | Django 项目配置 |
| `/home/www/gallery/manage.py` | Django 管理脚本 |
| `/home/www/gallery/gunicorn_config.py` | Gunicorn 配置 |
| `/home/www/gallery/venv/` | Python 虚拟环境 |
| `/home/www/gallery/db.sqlite3` | SQLite 数据库 |
| `/home/www/gallery/media/` | 用户上传的图片 |
| `/home/www/gallery/staticfiles/` | 收集的静态文件 |
| `/home/www/gallery/logs/` | 日志目录 |
| `/home/www/gallery/.env` | 环境变量 |

---

## 三、systemd 服务

服务名: `gallery`

配置文件: `/etc/systemd/system/gallery.service`

```ini
[Unit]
Description=Gallery Blog Django App
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/www/gallery
EnvironmentFile=/home/www/gallery/.env
ExecStart=/home/www/gallery/venv/bin/gunicorn blogproject.wsgi:application -c /home/www/gallery/gunicorn_config.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

关键行为:
- 开机自启
- 进程崩溃 3 秒后自动重启
- `systemctl reload` 平滑重载（不停服）

---

## 四、Nginx 配置

配置文件: `/etc/nginx/sites-available/gallery`

```nginx
client_max_body_size 20M;

server {
    listen 80;
    server_name 159.75.241.101;

    location /static/ {
        alias /home/www/gallery/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/www/gallery/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 五、Django 配置改动

`blogproject/settings.py` 改了三处:

```
原来                          →  现在
SECRET_KEY = '写死的值'         →  SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', ...)
DEBUG = True                   →  DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [...]          →  ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '...').split(',')
```

新增:
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

---

## 六、Git 配置

| | 地址 |
|---|---|
| 远程仓库 | `git@github.com:EL7314/gallery-blog.git` |
| 本地远程名 | `origin` |
| 分支 | `master` |
| .gitignore | 排除 `.venv/` `db.sqlite3` `media/` `*.sh` 等 |

---

## 七、常用运维命令

```bash
# 查看服务状态
sudo systemctl status gallery
sudo systemctl status nginx

# 重启服务
sudo systemctl restart gallery

# 查看日志
tail -f /home/www/gallery/logs/gunicorn_error.log
sudo tail -f /var/log/nginx/access.log

# 更新代码（从 GitHub）
cd /home/www/gallery && git pull origin master && sudo systemctl restart gallery

# Django 管理命令
cd /home/www/gallery && source venv/bin/activate
python manage.py createsuperuser
python manage.py migrate
python manage.py collectstatic --noinput
```

---

## 八、请求链路

```
浏览器 → http://159.75.241.101
  → Nginx :80
    ├─ /static/* → 直接返回静态文件
    ├─ /media/*  → 直接返回用户图片
    └─ 其他请求  → proxy_pass → Gunicorn :8000 → Django → SQLite
```
