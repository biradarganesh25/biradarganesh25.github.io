import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader

def markdown_with_frontmatter_to_html(markdown_file, template_file, output_file):
    # Read and parse the Markdown file with frontmatter
    with open(markdown_file, 'r') as file:
        post = frontmatter.load(file)
    
    # Extract content and metadata
    content = post.content
    metadata = post.metadata

    # Convert Markdown content to HTML
    html_content = markdown.markdown(content)
    
    # Load Jinja template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(template_file)

    # Render the template with HTML content and metadata
    rendered_html = template.render(content=html_content, **metadata)

    # Write the output to an HTML file
    with open(output_file, 'w') as file:
        file.write(rendered_html)

# Example usage
markdown_with_frontmatter_to_html('/home/gbiradar/Documents/biradarganesh25.github.io/content/python/tls_in_requests_lib.md', 'page.html', 'output.html')
