"""Template rendering helpers."""
from flask import render_template_string


PROFILE_TEMPLATE = """
<html>
<head><title>Profile</title></head>
<body>
<h1>User Profile</h1>
<!-- BUG 4: XSS vulnerability — user input rendered without escaping -->
<p>Welcome, {{ name | safe }}</p>
<p>Email: {{ email }}</p>
</body>
</html>
"""


def render_profile(name: str, email: str) -> str:
    """Render the user profile page."""
    return render_template_string(PROFILE_TEMPLATE, name=name, email=email)
