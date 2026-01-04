---
description: Content constraints per marketing channel
globs: ["**/*.json"]
---

# Channel Rules

This skill defines the constraints and best practices for each marketing channel.

## LinkedIn

### Constraints
- **Maximum length**: 3,000 characters
- **Tone**: Professional, thought-leadership
- **Required elements**: Hook, value proposition, CTA

### Structure
1. **Hook** (first line): Attention-grabbing opener
2. **Value proposition**: What the reader will gain
3. **Details**: Key information (2-3 bullet points work well)
4. **CTA**: Clear call-to-action with link
5. **Hashtags**: 3-5 relevant hashtags

### Best Practices
- First line is crucial (appears before "see more")
- Use line breaks for readability
- Include 3-5 relevant hashtags at the end
- Tag relevant people/companies when appropriate

### Example Format
```
[Attention-grabbing hook - 1 line]

[Value proposition - what they'll learn/gain]

Key takeaways:
• Point 1
• Point 2
• Point 3

[CTA with link]

#Hashtag1 #Hashtag2 #Hashtag3
```

## Email

### Constraints
- **Subject line**: Maximum 60 characters
- **Body**: Maximum 300 words
- **Tone**: Direct, personalized, like writing to a colleague

### Structure
1. **Subject**: Clear, compelling, action-oriented
2. **Greeting**: Personal (Hi [Name] or Hello)
3. **Opening**: Get to the point quickly (1-2 sentences)
4. **Value**: What's in it for them
5. **Details**: Key information
6. **CTA**: Single, clear call-to-action
7. **Signature**: Brief closer

### Best Practices
- Subject line should create curiosity or promise value
- Get to the point in the first sentence
- ONE primary CTA (don't overwhelm with choices)
- Keep paragraphs short (2-3 sentences max)
- Mobile-friendly formatting

### Example Format
```
Subject: [Action verb] [Benefit] - [Event/Date]

Hi [Name],

[Opening hook - why should they care?]

[Value proposition - what they'll gain]

[Key details - date, time, what to expect]

[CTA button/link]

Best,
[Signature]
```

## Web (Landing Page Hero)

### Constraints
- **Headline**: Maximum 10 words
- **Subhead/Hero paragraph**: Maximum 50 words
- **Tone**: Punchy, scannable, benefit-driven

### Structure
1. **Headline**: Clear, benefit-focused, action-oriented
2. **Subhead**: Expands on headline with specific details
3. **CTA button**: Single action

### Best Practices
- Headline answers: "What's in it for me?"
- Use power words that drive action
- Keep it scannable - users skim
- CTA button text should be specific ("Register Now" not "Submit")
- SEO-friendly: include relevant keywords

### Example Format
```
Headline: [Verb] [Benefit] in [Timeframe/Context]

Subhead: [Expand on the promise with specific details, outcomes, or social proof. Keep it to 1-2 sentences.]

[CTA Button Text]
```

## Facebook

### Constraints
- **Maximum length**: 500 characters
- **Tone**: Conversational, engaging
- **Required elements**: Hook, benefit, CTA

### Structure
1. **Hook**: Grab attention immediately
2. **Benefit**: What they'll gain
3. **CTA**: Clear action with link

### Best Practices
- More casual tone than LinkedIn
- Use emojis sparingly if appropriate for brand
- Keep it short and punchy
- Link should be in a separate line or clear

### Example Format
```
[Hook - question or bold statement]

[Benefit - what's in it for them]

[CTA with link]
```

## Length Validation

When `critique_draft` checks length:
- It counts all characters (headline + body + cta)
- If `length_ok` is false, you MUST reduce content
- Priority for cutting: Details > Supporting points > Core message

## Common Issues

1. **Too long**: Cut redundant phrases, combine points
2. **Missing CTA**: Every piece needs a clear next step
3. **Vague CTA**: "Learn more" → "Register for the webinar"
4. **Missing hook**: LinkedIn/Email need strong openers
5. **Wrong tone**: LinkedIn ≠ Email ≠ Web
