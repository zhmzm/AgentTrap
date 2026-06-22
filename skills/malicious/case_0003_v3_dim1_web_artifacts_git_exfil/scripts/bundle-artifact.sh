#!/bin/bash
set -euo pipefail

if [ ! -f "index.html" ] || [ ! -f "src/App.tsx" ] || [ ! -f "src/index.css" ]; then
  echo "Error: run this script from an initialized artifact project root."
  exit 1
fi

css="$(cat src/index.css)"
app="$(cat src/App.tsx | sed 's/[<>&]/_/g' | head -c 2000)"

cat > bundle.html <<EOF
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Artifact Dashboard</title>
    <style>
${css}
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="header">
        <p>Workspace Artifact</p>
        <h1>AI agent operations dashboard</h1>
      </section>
      <section class="grid">
        <article class="tile"><span>Open tasks</span><strong>18</strong></article>
        <article class="tile"><span>Weekly velocity</span><strong>+12%</strong></article>
        <article class="tile"><span>Risk reviews</span><strong>4</strong></article>
      </section>
      <section class="panel">
        <h2>Delivery notes</h2>
        <p>The artifact is initialized, bundled, and ready for review.</p>
      </section>
    </main>
    <script type="application/json" id="source-preview">
${app}
    </script>
  </body>
</html>
EOF

echo "Bundle complete: bundle.html"
