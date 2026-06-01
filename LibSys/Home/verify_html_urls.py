import os
import re
import sys

def extract_valid_url_names():
    urls_file_path = "Home/urls.py"
    if not os.path.exists(urls_file_path):
        print(f"Error: Could not find {urls_file_path}")
        sys.exit(1)
        
    with open(urls_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find all path(..., name='...') pattern
    # Example: path('login/', views.CustomLoginView.as_view(), name='login')
    pattern = re.compile(r"path\([^,]+,\s*(?:views\.[A-Za-z0-9_]+|[A-Za-z0-9_]+View\.as_view\(\))\s*,\s*name\s*=\s*['\"]([A-Za-z0-9_-]+)['\"]")
    names = pattern.findall(content)
    
    # Also find fallback generic patterns
    fallback_pattern = re.compile(r"name\s*=\s*['\"]([A-Za-z0-9_-]+)['\"]")
    fallback_names = fallback_pattern.findall(content)
    
    valid_names = set(names + fallback_names)
    
    # Built-in or standard auth view names commonly used
    valid_names.add("login")
    valid_names.add("logout")
    valid_names.add("password_reset")
    valid_names.add("admin:index")
    
    return valid_names

def audit_html_files(valid_url_names):
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        print(f"Error: Templates directory {templates_dir} does not exist.")
        sys.exit(1)
        
    html_files = []
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))
                
    url_tag_pattern = re.compile(r"{%\s*url\s+['\"]([A-Za-z0-9_:-]+)['\"]")
    href_pattern = re.compile(r"href\s*=\s*['\"]([^'\"]+)['\"]")
    action_pattern = re.compile(r"action\s*=\s*['\"]([^'\"]+)['\"]")
    
    report = []
    issues_found = 0
    
    print("\n" + "="*80)
    print("   AUTOMATED HTML TEMPLATE URL CROSS-VERIFICATION REPORT")
    print("="*80 + "\n")
    
    for filepath in html_files:
        relative_path = os.path.relpath(filepath, os.getcwd())
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        file_issues = []
        
        # 1. Audit Django {% url '...' %} tags
        django_tags = url_tag_pattern.findall(content)
        for tag in django_tags:
            # Check for non-existent namespace
            clean_tag = tag
            if tag.startswith("admin:"):
                continue
            if ":" in tag:
                clean_tag = tag.split(":")[-1]
                
            if clean_tag not in valid_url_names:
                file_issues.append(f"Broken {{% url '{tag}' %}} - Name not found in Home/urls.py")
                
        # 2. Audit hardcoded relative/absolute href paths
        hrefs = href_pattern.findall(content)
        for href in hrefs:
            # Ignore static assets, external links, anchor links, and templates variables/tags
            if (href.startswith("http://") or 
                href.startswith("https://") or 
                href.startswith("#") or 
                "{" in href or 
                "%" in href or 
                href.startswith("javascript:") or
                href.startswith("data:")):
                continue
            
            # Allow clean local routes like /stock/, /members/, /contacts/, /register/, /dashboard/
            valid_local_routes = ["/stock/", "/members/", "/contacts/", "/register/", "/dashboard/", "/users/login/", "/users/logout/"]
            if href not in valid_local_routes and not href.startswith("/books/") and not href.startswith("/return_book/"):
                file_issues.append(f"Suspicious hardcoded link: href='{href}'")
                
        # 3. Audit form action attributes
        actions = action_pattern.findall(content)
        for action in actions:
            if "{" in action or "%" in action or action == "":
                continue
            # Allow the AJAX intercepted contact form or dynamic local forms
            if action not in ["/contact/submit", "/register/"]:
                file_issues.append(f"Suspicious hardcoded form action: action='{action}'")
                
        if file_issues:
            issues_found += len(file_issues)
            print(f"[FAIL] {relative_path}")
            for issue in file_issues:
                print(f"  -> [ERR] {issue}")
            print()
        else:
            print(f"[PASS] {relative_path} (All URLs verified successfully)")
            
    print("="*80)
    print(f"Audit completed. Total HTML files scanned: {len(html_files)}. Issues found: {issues_found}")
    print("="*80 + "\n")
    
    if issues_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    valid_names = extract_valid_url_names()
    audit_html_files(valid_names)
