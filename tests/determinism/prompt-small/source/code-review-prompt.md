<system>
You are an expert code reviewer. Analyze the provided code for bugs, style issues, and security concerns.
</system>

<user>
Review the following Python function:

```python
def process_items(items):
    result = []
    for i in range(len(items)):
        item = items[i]
        if item.active:
            result.append(item.name)
    return result
```
</user>

<output_format>
Return a JSON object with:
- `findings`: array of issues found
- `score`: overall quality score 0-10
</output_format>

<verification>
Before submitting, verify:
- All active items are included in the output
- No inactive items appear in the output
- Score is within 0-10 range
</verification>
