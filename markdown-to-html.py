import frontmatter
import pypandoc
from jinja2 import Environment, FileSystemLoader
import os

def convert_and_render_with_frontmatter(source_directory, target_directory, template_file):
    # Read and parse the Markdown file with frontmatter
    markdown_files = []
    # Walk through all the md files in source_directory
    for root, dirs, files in os.walk(source_directory):
        for file in files:
            if file.endswith(".md"):
                # Construct the full file path of md files
                full_path = os.path.join(root, file)

                # Create corresponding directory structure in target_directory
                relative_dir = os.path.relpath(root, source_directory)
                target_dir = os.path.join(target_directory, relative_dir, file)
                target_dir = target_dir.rsplit('.', 1)[0]
                os.makedirs(target_dir, exist_ok=True)

                # Convert the full path of md files in source_directory to a URL-like string
                url = os.path.relpath(full_path, source_directory).replace(os.path.sep, '/')
                # Exclude the '.md' extension from the URL
                url = url.rsplit('.', 1)[0]

                # Print the absolute path of the markdown file
                absolute_path = os.path.abspath(full_path)
                print(absolute_path)

                with open(absolute_path, 'r') as file:
                    post = frontmatter.load(file)
                
                # Extract content and metadata
                content = post.content
                metadata = post.metadata

                markdown_files.append({'url':url, 'name': metadata['title']})

                # Convert Markdown content to HTML using Pandoc
                html_content = pypandoc.convert_text(content, 'html', format='md', extra_args=['--highlight-style', 'pygments'])

                # Load the Jinja template
                env = Environment(loader=FileSystemLoader('./templates'))
                template = env.get_template(template_file)

                # Render the template with HTML content and metadata
                rendered_html = template.render(content=html_content, **metadata)

                # Write the output to an HTML file
                with open(os.path.join(target_dir,'index.html'), 'w') as file:
                    file.write(rendered_html)

                # Write the index file
                rendered_html = env.get_template('index.html').render(files=markdown_files)

                with open(os.path.join('docs', 'index.html'), 'w') as file: 
                    file.write(rendered_html)

# Directory containing your markdown files
content_directory = 'content'

convert_and_render_with_frontmatter('content', 'docs', 'page.html')
