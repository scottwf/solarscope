# SolarScope Admin Page Refactor Instructions

These steps outline how to reorganize `app/templates/admin.html` into clearly separated sections for **Settings** and **Functions/Tools**.

## Objective
- Group persistent configuration (API keys, electricity cost, weather location, etc.) under a **Settings** heading.
- Group one‑off actions (file uploads, data imports, password changes) under a **Functions & Tools** heading.
- Maintain existing form functionality while improving layout and readability using Tailwind CSS.

## Steps
1. **Create the Settings Section**
   - Wrap the following forms/inputs in a `<section>` element near the top of the page:
     - SolarEdge API Key and Site ID form
     - Electricity cost input
     - Weather location form (city/coordinates)
     - Weather import start date (if present)
   - Prepend the section with a heading:
     ```html
     <h2 class="text-lg font-semibold mb-4">Settings</h2>
     ```
   - Use Tailwind utility classes (`mb-8`, `p-4`, `bg-white`, `rounded`, etc.) to style the card or panel containing these items.

2. **Create the Functions & Tools Section**
   - Below the Settings block, create another `<section>` for action‑oriented tasks:
     - File upload (usage CSV)
     - SolarEdge data import (single and batch)
     - Weather data fetch
     - Password change form
   - Add a heading:
     ```html
     <h2 class="text-lg font-semibold mb-4">Functions &amp; Tools</h2>
     ```
   - Each function can be placed in its own `<div class="mb-6">` for clarity.

3. **Section Order and Separation**
   - Display the Settings section first, followed by a divider (`<div class="my-4 border-b border-gray-200"></div>`) before the Functions & Tools section.
   - Ensure consistent spacing and margins (`mb-4`, `mt-6`) between forms.

4. **Accessibility and Labels**
   - Verify that each input has an associated `<label>` element.
   - Use semantic headings (`<h2>`, `<h3>`) to aid screen readers.

5. **Optional Enhancements**
   - If the page becomes long, add a sticky sidebar or table of contents linking to the Settings and Functions sections.
   - Provide brief help text or tooltips for complex fields (e.g., API key).

## Deliverable
A revised `admin.html` file with two clearly defined sections that separate configuration settings from functional tools. All existing functionality must remain intact, but the layout should be easier to scan and maintain.
