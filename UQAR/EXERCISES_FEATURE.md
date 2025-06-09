# Automatic Exercise Generation Feature

## Overview

This document describes the new automatic exercise generation feature added to the UQAR educational chatbot platform. This feature allows teachers to automatically generate exercises based on uploaded course content, which students can then complete and receive automatic feedback.

## Architecture

### Database Schema Changes

#### New Tables

1. **questions** - Stores individual questions for exercises
   - `id`: Primary key
   - `exercise_id`: Foreign key to exercises table
   - `text`: The question text
   - `question_type`: Type of question (mcq, open_ended, true_false, fill_blank)
   - `options`: JSON array of options for MCQ questions
   - `correct_answer`: The correct answer
   - `expected_keywords`: JSON array of keywords for open-ended questions
   - `explanation`: Explanation of the answer
   - `points`: Points value for the question
   - `order_index`: Display order

2. **exercise_submissions** - Stores student submissions
   - `id`: Primary key
   - `exercise_id`: Foreign key to exercises
   - `student_id`: Foreign key to users
   - `answers`: JSON object mapping question_id to answer
   - `score`: Total points earned
   - `percentage`: Percentage score
   - `feedback`: JSON array of feedback for each question
   - `submitted_at`: Submission timestamp

#### Modified Tables

1. **exercises** - Updated structure
   - Removed: `title`, `question`, `exercise_data`, `is_validated`, etc.
   - Added: `status` (enum: generating, pending, validated)
   - Added: `generation_params` (JSON)
   - Added: `source_documents` (JSON)
   - Added: `created_at`, `updated_at` timestamps

### Backend Components

#### Services

1. **ExerciseGenerationService** (`/backend/app/services/exercise_service.py`)
   - Generates exercises using Ollama LLM
   - Retrieves relevant content from ChromaDB
   - Creates structured questions based on course material

2. **ExerciseFeedbackService** (`/backend/app/services/exercise_service.py`)
   - Generates pedagogical feedback for student answers
   - Uses Ollama to provide contextual explanations

3. **ChromaService** (`/backend/app/services/chroma_service.py`)
   - Provides interface to query ChromaDB collections
   - Retrieves relevant document chunks for exercise generation

#### API Endpoints

All endpoints are in `/backend/app/api/exercises.py`:

**Teacher Endpoints:**
- `POST /api/exercises/sections/{section_id}/exercises/generate` - Generate new exercises
- `GET /api/exercises/sections/{section_id}/exercises` - Get exercises for a section
- `PUT /api/exercises/exercises/{exercise_id}/validate` - Validate an exercise
- `DELETE /api/exercises/exercises/{exercise_id}` - Delete an exercise

**Student Endpoints:**
- `GET /api/exercises/exercises/{exercise_id}` - Get exercise details
- `POST /api/exercises/exercises/{exercise_id}/submit` - Submit exercise answers
- `GET /api/exercises/exercises/{exercise_id}/submissions` - Get submissions

#### Schemas

Exercise schemas are defined in `/backend/app/schemas/exercise_schemas.py`:
- `ExerciseGenerateRequest` - Request model for exercise generation
- `ExerciseResponse` - Response model for exercises
- `ExerciseSubmission` - Model for student submissions
- `ExerciseResult` - Model for submission results with feedback

### Frontend Components

#### Teacher Interface

**Page:** `/frontend/src/pages/teacher/exercises.tsx`

Features:
- Section selector to choose which course section
- Exercise generation form with options:
  - Number of questions (1-20)
  - Difficulty level (easy, medium, hard)
  - Question type (MCQ, open-ended, true/false, fill-blank)
- Exercise list showing:
  - Status (generating, pending, validated)
  - Questions with answers and explanations
  - Validation button for pending exercises

#### Student Interface

**Page:** `/frontend/src/pages/student/exercises.tsx`

Features:
- Section selector to view exercises by course
- Exercise list (only validated exercises shown)
- Exercise taking interface:
  - Display questions based on type
  - Input controls for answers
  - Submit functionality
- Result display:
  - Individual question feedback
  - Score and percentage
  - Pedagogical explanations

## User Workflows

### Teacher Workflow

1. **Navigate to Exercises Page**
   - Access from teacher dashboard navigation

2. **Select Section**
   - Choose the course section for exercise generation

3. **Configure Exercise Parameters**
   - Set number of questions
   - Choose difficulty level
   - Select question type

4. **Generate Exercises**
   - Click "Generate Exercises" button
   - System retrieves relevant content from ChromaDB
   - Ollama generates questions based on content

5. **Review Generated Exercises**
   - View all questions with answers and explanations
   - Check quality and relevance

6. **Validate Exercises**
   - Click "Validate" for approved exercises
   - Add validation notes if needed
   - Validated exercises become visible to students

### Student Workflow

1. **Navigate to Exercises Page**
   - Access from student dashboard or section card

2. **Select Section**
   - Choose course section to view exercises

3. **Choose Exercise**
   - Select from list of validated exercises

4. **Complete Exercise**
   - Answer all questions
   - Use appropriate input controls per question type

5. **Submit Answers**
   - Click submit when all questions answered
   - Receive immediate feedback

6. **Review Results**
   - View score and percentage
   - Read feedback for each question
   - See correct answers and explanations

## Technical Implementation Details

### Exercise Generation Process

1. **Content Retrieval**
   - Query ChromaDB for relevant document chunks
   - Filter by section's collection name
   - Optional: Filter by specific document IDs

2. **Prompt Construction**
   - Build system prompt with exercise parameters
   - Include course content in user prompt
   - Specify JSON output format

3. **LLM Generation**
   - Send prompt to Ollama
   - Parse JSON response
   - Validate question structure

4. **Database Storage**
   - Create exercise with "generating" status
   - Save questions with proper relationships
   - Update status to "pending"

### Answer Evaluation

1. **MCQ & True/False**
   - Direct comparison with correct answer
   - Binary correct/incorrect evaluation

2. **Open-Ended Questions**
   - Keyword matching (50% threshold)
   - LLM-based feedback generation

3. **Fill in the Blank**
   - Exact or fuzzy matching
   - Case-insensitive comparison

### Security Considerations

- Teachers can only generate/validate exercises for their own sections
- Students can only see validated exercises
- Students can only see their own submissions
- All endpoints require authentication
- Role-based access control enforced

## Migration Guide

To update an existing installation:

1. **Run Database Migration**
   ```bash
   cd backend
   python -m app.scripts.migrate_exercises
   ```

2. **Update Backend Dependencies**
   - No new dependencies required

3. **Update Frontend Routes**
   - Add exercises pages to routing configuration
   - Update navigation menus

4. **Test the Feature**
   - Create test exercises as teacher
   - Validate and test as student

## Configuration

No additional configuration required. The feature uses existing:
- Ollama configuration for LLM
- ChromaDB configuration for vector search
- Upload directory for document storage

## Troubleshooting

### Common Issues

1. **Exercise Generation Fails**
   - Check Ollama service is running
   - Verify ChromaDB is accessible
   - Ensure section has uploaded documents

2. **No Content Found Error**
   - Verify documents are vectorized
   - Check ChromaDB collection exists
   - Ensure documents have extracted text

3. **Validation Not Working**
   - Confirm user is section teacher
   - Check exercise status is "pending"
   - Verify database permissions

### Logging

Enable debug logging for troubleshooting:
```python
# In backend configuration
LOG_LEVEL = "DEBUG"
```

Key log locations:
- Exercise generation: `exercise_service.py`
- ChromaDB queries: `chroma_service.py`
- API requests: `exercises.py`

## Future Enhancements

1. **Batch Exercise Generation**
   - Generate multiple exercise sets at once
   - Schedule automatic generation

2. **Advanced Question Types**
   - Code completion exercises
   - Diagram labeling
   - Mathematical equations

3. **Analytics Dashboard**
   - Student performance tracking
   - Question difficulty analysis
   - Learning progress visualization

4. **Collaborative Features**
   - Exercise sharing between teachers
   - Student peer review
   - Group exercises

5. **Adaptive Learning**
   - Difficulty adjustment based on performance
   - Personalized exercise recommendations
   - Learning path optimization 