import os
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import yaml
import markdown
from datetime import date

def parse_front_matter(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Split the content into front matter and HTML
    parts = content.split('---', 2)
    if len(parts) == 3:
        front_matter = yaml.safe_load(parts[1])
        markdown_content = parts[2]
    else:
        front_matter = {}
        markdown_content = content
    
    print(f"front_matter: {front_matter}")
    return front_matter, markdown_content

def convert_markdown_to_html(markdown_content):
    html_content = markdown.markdown(markdown_content, extensions=['extra'])
    return html_content

def generate_static_site(blog_posts_dir, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))

    # Get all blog post files
    blog_posts = []
    for root, _, files in os.walk(blog_posts_dir):
        for file in files:
            if file.endswith('.md'):
                rel_path = os.path.relpath(os.path.join(root, file), blog_posts_dir)
                url = rel_path.split('.')[0]+'.html'
                blog_posts.append({"url": url, "name": file, "path": rel_path})


    tags = {}
    # Process each blog post
    post_template = env.get_template('page.html')
    for post in blog_posts:
        # Read the content of the blog post
        post_front_matter, post_content = parse_front_matter(os.path.join(blog_posts_dir, post["path"]))
        post_content = convert_markdown_to_html(post_content)
        for tag in post_front_matter["tags"]:
            if tag not in tags:
                tags[tag] = []
            tags[tag].append({"url": post["url"], "title": post_front_matter["title"]})
        
        post["title"] = post_front_matter["title"]
        post["published_date"] = date.fromisoformat(post_front_matter["published_date"])

        # Render the post template
        output = post_template.render(content=post_content, title=post["title"])

        # Write the rendered post to the output directory
        output_path = os.path.join(output_dir, post["url"])
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(output)

    # Generate index.html
    index_template = env.get_template('index.html')
    index_content = index_template.render(blog_posts=blog_posts)
    with open(os.path.join(output_dir, 'index.html'), 'w') as f:
        f.write(index_content)
    
    print(f"tags: {tags}")
    tags_template = env.get_template("tags.html")
    output = tags_template.render(tags=tags)
    output_path = os.path.join(output_dir, "tags.html")
    with open(output_path, "w") as f:
        f.write(output)

if __name__ == "__main__":
    blog_posts_dir = 'html_content'
    output_dir = 'docs'
    generate_static_site(blog_posts_dir, output_dir)