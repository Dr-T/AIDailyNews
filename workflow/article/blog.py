import os
from datetime import datetime
from dateutil import tz


class Blog:
    metadata: str
    guide: str
    categories: list

    def __init__(self, metadata, guide, categories):
        self.metadata = metadata
        self.guide = guide
        self.categories = categories

    def make_blog(self):
        return self.metadata + self.guide + "\n".join(self.categories)


def make_daily_markdown_with(articles):
    tags = []
    article_titles = []

    for article in articles:
        tags.extend(article.evaluate.get("tags", []))
        article_titles.append(article.evaluate["title"])

    md_path, meta_data = make_meta_data(description="\n".join(article_titles), tags=tags)
    daily_guide = make_daily_guide(article_titles)

    # TODO: 仅用于控制展示顺序，命名需跟resources文件一致
    category_list = ["Daily News", "Daily Blog", "Daily Code"]
    category_contents = []
    for category in category_list:
        category_contents.append(make_daily_category(category=category, articles=articles))

    blog = Blog(metadata=meta_data, guide=daily_guide, categories=category_contents)
    print(f"make blog success: {meta_data}")
    with open(md_path, "w") as fp:
        fp.write(blog.make_blog())
        print(f"write to file: {md_path}")


def make_meta_data(description, tags):

    time_zone = tz.gettz("Asia/Shanghai")
    today_with_timezone = datetime.today().astimezone(time_zone)
    today_str = today_with_timezone.strftime("%Y-%m-%d")

    current_directory = os.path.dirname(os.path.abspath(__file__))
    # 获取当前项目的根目录
    project_root = os.path.dirname(current_directory)
    blog_folder = f"{project_root}/../src/content/blog"

    md_title = f"iOS Daily News #{today_str}"

    tags_str = "".join([f"- '{tag}'\n" for tag in set(tags)])

    data = f"""---
title: "{md_title}"
date: "{today_with_timezone.strftime("%Y-%m-%d %H:%M:%S")}"
author: 摸鱼仔
description: "{description}"
tags: 
{tags_str}
---
"""

    path = f"{blog_folder}/iOSDailyNews_{today_str}.md"

    return path, data


def make_daily_category(category, articles):
    if not articles:
        return ""
    content = ""
    for article in articles:
        if article.category != category:
            continue
        article_intro = f"""
### [{article.evaluate["title"]}]({article.link})

来源：{article.info["title"]}

发布时间：{article.date}

{article.evaluate["summary"]}
"""
        content += article_intro
    if content:
        content = f"## {category}\n" + content
    return content


def make_daily_guide(titles):
    guide = "".join([f"> * {item}\n" for item in titles])
    return f"\n{guide}\n"
