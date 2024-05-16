import re

html_string = '<template><div>hello</div><template><p>world</p></template></template>'

start_tag = re.search(r'<template>', html_string).end()
end_tag = html_string.rindex('</template>')

raw_content = html_string[start_tag:end_tag]
print(raw_content)  # Output: <div>hello</div><template><p>world</p></template>