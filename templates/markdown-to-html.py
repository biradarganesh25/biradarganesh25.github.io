import frontmatter
import pypandoc
from jinja2 import Environment, FileSystemLoader

def convert_and_render_with_frontmatter(markdown_file, template_file, output_file):
    # Read and parse the Markdown file with frontmatter
    with open(markdown_file, 'r') as file:
        post = frontmatter.load(file)
    
    # Extract content and metadata
    content = post.content
    metadata = post.metadata

    # Convert Markdown content to HTML using Pandoc
    html_content = pypandoc.convert_text(content, 'html', format='md')

    # Load the Jinja template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(template_file)

    # Render the template with HTML content and metadata
    rendered_html = template.render(content=html_content, **metadata)

    # Write the output to an HTML file
    with open(output_file, 'w') as file:
        file.write(rendered_html)

# Example usage
# convert_and_render_with_frontmatter('example.md', 'template.html', 'output.html')


# Example usage
convert_and_render_with_frontmatter('/home/gbiradar/Documents/biradarganesh25.github.io/content/python/tls_in_requests_lib.md', 'page.html', 'output.html')
