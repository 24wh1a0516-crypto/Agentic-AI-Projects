# AI Quiz Generator - Specification Document

## 1. Project Overview

### Project Name

AI-Powered Quiz Generator

### Description

An AI-based web application that transforms PowerPoint presentations (.ppt/.pptx) into interactive multiple-choice quizzes.

The system extracts content from uploaded presentations, generates quiz questions using an LLM (DeepSeek), and provides an interactive quiz experience with scoring and detailed explanations.

---

# 2. Objectives

* Upload PowerPoint files.
* Extract slide content automatically.
* Generate AI-based MCQs.
* Support multiple difficulty levels.
* Provide an interactive quiz interface.
* Calculate scores automatically.
* Generate explanations for incorrect answers.

---

# 3. Scope

## In Scope

* PPT/PPTX Upload
* Slide Text Extraction
* AI Question Generation
* Difficulty Selection
* Interactive Quiz
* Score Calculation
* Answer Review
* AI Explanations

## Out of Scope

* User Authentication
* Database Persistence
* Multi-language Support
* Essay Questions
* Audio/Video Inputs

---

# 4. Technology Stack

## Frontend

* React.js
* Vite
* Tailwind CSS
* Axios

## Backend

* Spring Boot
* Java 21
* Apache POI
* Jackson

## AI

* DeepSeek API

## Deployment

* Frontend: Vercel / Netlify
* Backend: Render / Railway

---

# 5. System Architecture

User
↓
React Frontend
↓
Spring Boot Backend
↓
PPT Parser (Apache POI)
↓
Prompt Builder
↓
DeepSeek API
↓
Generated Quiz
↓
Frontend Quiz UI

---

# 6. Functional Requirements

## FR-01 File Upload

### Description

Allow users to upload PowerPoint files.

### Inputs

* .ppt
* .pptx

### Validation

* Maximum Size: 20 MB
* Allowed Extensions:

  * .ppt
  * .pptx

### Output

* File Accepted
* Slide Count
* Preview Text

---

## FR-02 PPT Parsing

### Description

Extract all textual content from uploaded slides.

### Responsibilities

* Read all slides
* Extract text
* Ignore animations
* Combine content

### Output

Extracted Text String

---

## FR-03 Quiz Configuration

### Inputs

Question Count:

* Minimum: 5
* Maximum: 30

Difficulty:

* Simple
* Medium
* Complex

### Output

Quiz Generation Request

---

## FR-04 AI MCQ Generation

### Description

Generate quiz questions from extracted PPT content.

### Rules

* Exactly 4 options
* One correct answer
* No duplicates
* Relevant to slide content

### Output Schema

{
"question": "",
"options": [
"",
"",
"",
""
],
"correctAnswer": "",
"explanation": ""
}

---

## FR-05 Quiz Interface

### Features

* One question per screen
* Option selection
* Next button
* Previous button
* Submit Quiz

### Optional

* Timer

---

## FR-06 Scoring System

### Formula

Score =
(Number of Correct Answers / Total Questions) × 100

### Outputs

* Total Score
* Correct Answers
* Wrong Answers
* Percentage

---

## FR-07 Feedback Module

For every incorrect answer:

Display:

* Correct Option
* User Option
* AI Explanation

---

# 7. Non-Functional Requirements

## Performance

* Upload Response < 3 sec
* Quiz Generation < 15 sec

## Scalability

* Support 100 concurrent users
