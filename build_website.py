import os
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

def generate_static_site(blog_posts_dir, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))

    # Get all blog post files
    blog_posts = []
    for root, _, files in os.walk(blog_posts_dir):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), blog_posts_dir)
                blog_posts.append({"url": rel_path, "name": file})

    # Generate index.html
    index_template = env.get_template('index.html')
    index_content = index_template.render(blog_posts=blog_posts)
    with open(os.path.join(output_dir, 'index.html'), 'w') as f:
        f.write(index_content)

    # Process each blog post
    post_template = env.get_template('page.html')
    for post in blog_posts:
        # Read the content of the blog post
        with open(os.path.join(blog_posts_dir, post["url"]), 'r') as f:
            post_content = f.read()

        # Render the post template
        output = post_template.render(content=post_content)

        # Write the rendered post to the output directory
        output_path = os.path.join(output_dir, post["url"])
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(output)

if __name__ == "__main__":
    blog_posts_dir = 'html_content'
    output_dir = 'output'
    generate_static_site(blog_posts_dir, output_dir)