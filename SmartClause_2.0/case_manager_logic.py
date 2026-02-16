"""
Case Manager Logic - Kenyan Legal System
Handles case management operations, AI integration, and deadline calculations
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, date
from database import DatabaseManager
import openai
import os

logger = logging.getLogger(__name__)


class CaseManager:
    """Manages legal cases with AI integration for Kenyan legal system."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        
        # Initialize OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            openai.api_key = api_key
        else:
            logger.warning("OpenAI API key not found. AI features will be disabled.")
    
    # ==================== Case Management ====================
    
    def create_case(
        self,
        matter_id: str,
        user_id: str,
        organization_id: Optional[str],
        case_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new case.
        
        Args:
            matter_id: Matter ID this case belongs to
            user_id: User creating the case
            organization_id: Organization ID (if applicable)
            case_data: Case details (case_number, case_type, etc.)
        
        Returns:
            Created case dict or None
        """
        try:
            case = self.db.create_case(
                matter_id=matter_id,
                user_id=user_id,
                organization_id=organization_id,
                **case_data
            )
            
            if case:
                # Auto-generate initial tasks based on case type and stage
                self._generate_initial_tasks(case['id'], case_data.get('case_type'), case_data.get('current_stage'))
            
            return case
        except Exception as e:
            logger.error(f"Error creating case: {e}", exc_info=True)
            return None
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get case by ID."""
        return self.db.get_case(case_id)
    
    def update_case(self, case_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update case details."""
        return self.db.update_case(case_id, updates)
    
    def get_cases_for_matter(self, matter_id: str) -> List[Dict[str, Any]]:
        """Get all cases for a matter."""
        return self.db.get_cases_by_matter(matter_id)
    
    # ==================== Case Events ====================
    
    def add_event(self, case_id: str, event_data: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        """Add an event to case timeline."""
        event_data['created_by'] = user_id
        return self.db.create_case_event(case_id, event_data)
    
    def get_case_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        """Get chronological timeline of case events."""
        return self.db.get_case_events(case_id)
    
    # ==================== Task Management ====================
    
    def create_task(
        self,
        case_id: str,
        task_data: Dict[str, Any],
        user_id: str,
        ai_generated: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Create a case task."""
        task_data['created_by'] = user_id
        task_data['ai_generated'] = ai_generated
        return self.db.create_case_task(case_id, task_data)
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update task details."""
        return self.db.update_case_task(task_id, updates)
    
    def complete_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Mark task as completed."""
        return self.db.update_case_task(task_id, {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'completed_by': user_id
        })
    
    def get_case_tasks(self, case_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks for a case, optionally filtered by status."""
        return self.db.get_case_tasks(case_id, status)
    
    def get_overdue_tasks(self, case_id: str) -> List[Dict[str, Any]]:
        """Get overdue tasks for a case."""
        all_tasks = self.db.get_case_tasks(case_id)
        today = date.today()
        
        overdue = []
        for task in all_tasks:
            if task['status'] not in ['completed', 'cancelled']:
                due_date = task.get('due_date')
                if due_date:
                    if isinstance(due_date, str):
                        due_date = datetime.fromisoformat(due_date).date()
                    if due_date < today:
                        overdue.append(task)
        
        return overdue
    
    # ==================== Document Linking ====================
    
    def link_document(
        self,
        case_id: str,
        document_id: str,
        document_type: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Link a document to a case."""
        link_data = {
            'document_type': document_type,
            'uploaded_by': user_id,
            **(metadata or {})
        }
        return self.db.link_document_to_case(case_id, document_id, link_data)
    
    def get_case_documents(self, case_id: str) -> List[Dict[str, Any]]:
        """Get all documents linked to a case."""
        return self.db.get_case_documents(case_id)
    
    # ==================== Case Notes ====================
    
    def add_note(
        self,
        case_id: str,
        note_text: str,
        note_type: str,
        user_id: str,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Add a note to a case."""
        note_data = {
            'note_text': note_text,
            'note_type': note_type,
            'tags': tags or [],
            'created_by': user_id
        }
        return self.db.create_case_note(case_id, note_data)
    
    def get_case_notes(self, case_id: str, note_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get case notes, optionally filtered by type."""
        return self.db.get_case_notes(case_id, note_type)
    
    # ==================== AI Integration ====================
    
    def analyze_case(self, case_id: str) -> Dict[str, Any]:
        """
        Perform AI analysis on case.
        
        Returns:
            Dict with summary, risk_assessment, and strategy_suggestions
        """
        try:
            case = self.get_case(case_id)
            if not case:
                return {"error": "Case not found"}
            
            # Get case context
            events = self.get_case_timeline(case_id)
            documents = self.get_case_documents(case_id)
            notes = self.get_case_notes(case_id, 'legal_issue')
            
            # Build prompt for AI
            prompt = self._build_case_analysis_prompt(case, events, documents, notes)
            
            # Call OpenAI
            if not openai.api_key:
                return {"error": "AI features not configured"}
            
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a legal AI assistant specializing in Kenyan law. Analyze the case and provide objective assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse and structure the response
            analysis = self._parse_ai_analysis(analysis_text)
            
            # Update case with AI analysis
            self.db.update_case(case_id, {
                'ai_case_summary': analysis.get('summary'),
                'ai_risk_assessment': analysis.get('risk_assessment'),
                'ai_strategy_suggestions': analysis.get('strategies'),
                'last_ai_analysis_at': datetime.now().isoformat()
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing case: {e}", exc_info=True)
            return {"error": str(e)}
    
    def suggest_tasks(self, case_id: str, case_stage: str) -> List[Dict[str, Any]]:
        """Generate AI-powered task suggestions based on case stage."""
        try:
            tasks = self._get_kenyan_court_tasks(case_stage)
            
            # Create tasks in database
            created_tasks = []
            for task in tasks:
                created = self.create_task(
                    case_id=case_id,
                    task_data=task,
                    user_id=None,  # System-generated
                    ai_generated=True
                )
                if created:
                    created_tasks.append(created)
            
            return created_tasks
            
        except Exception as e:
            logger.error(f"Error suggesting tasks: {e}", exc_info=True)
            return []
    
    # ==================== Kenyan Court Deadlines ====================
    
    def calculate_deadline(self, base_date: date, deadline_type: str, court_level: str = 'high_court') -> date:
        """
        Calculate deadline based on Kenyan court rules.
        
        Args:
            base_date: Starting date
            deadline_type: Type of deadline (e.g., 'defence', 'reply', 'application')
            court_level: Court level
        
        Returns:
            Deadline date
        """
        # Kenyan court deadlines (in days)
        deadlines = {
            'high_court': {
                'defence': 14,  # 14 days to file defence
                'reply': 7,     # 7 days to file reply
                'rejoinder': 7,  # 7 days to file rejoinder
                'application_response': 7,  # 7 days to respond to application
                'written_submissions': 14,  # 14 days for submissions
            },
            'magistrate': {
                'defence': 14,
                'reply': 7,
                'application_response': 7,
            },
            'court_of_appeal': {
                'notice_of_appeal': 14,
                'record_of_appeal': 60,
                'written_submissions': 21,
            }
        }
        
        days = deadlines.get(court_level, {}).get(deadline_type, 14)
        return base_date + timedelta(days=days)
    
    # ==================== Helper Methods ====================
    
    def _generate_initial_tasks(self, case_id: str, case_type: Optional[str], stage: Optional[str]):
        """Auto-generate initial tasks based on case type and stage."""
        if not stage:
            return
        
        tasks = self._get_kenyan_court_tasks(stage)
        
        for task_data in tasks:
            self.create_task(case_id, task_data, user_id=None, ai_generated=True)
    
    def _get_kenyan_court_tasks(self, stage: str) -> List[Dict[str, Any]]:
        """Get standard tasks for Kenyan court proceedings based on stage."""
        task_templates = {
            'filing': [
                {
                    'title': 'Prepare and file plaint/petition',
                    'description': 'Draft and file the plaint/petition with court',
                    'task_type': 'filing',
                    'priority': 'high',
                    'due_date': (date.today() + timedelta(days=7)).isoformat(),
                },
                {
                    'title': 'Serve defendant/respondent',
                    'description': 'Serve filed documents on opposing party',
                    'task_type': 'filing',
                    'priority': 'high',
                    'due_date': (date.today() + timedelta(days=14)).isoformat(),
                }
            ],
            'pleadings': [
                {
                    'title': 'File defence (if defendant)',
                    'description': 'Prepare and file defence within 14 days',
                    'task_type': 'filing',
                    'priority': 'urgent',
                    'due_date': (date.today() + timedelta(days=14)).isoformat(),
                },
                {
                    'title': 'Review defence and consider reply',
                    'description': 'Review defence filed and determine if reply needed',
                    'task_type': 'drafting',
                    'priority': 'high',
                }
            ],
            'interlocutory': [
                {
                    'title': 'Prepare for interlocutory applications',
                    'description': 'Draft necessary applications (discovery, amendments, etc.)',
                    'task_type': 'drafting',
                    'priority': 'medium',
                }
            ],
            'hearing': [
                {
                    'title': 'Prepare hearing bundle',
                    'description': 'Compile all documents for court hearing',
                    'task_type': 'hearing_prep',
                    'priority': 'high',
                    'due_date': (date.today() + timedelta(days=7)).isoformat(),
                },
                {
                    'title': 'Brief witnesses',
                    'description': 'Meet and prepare witnesses for testimony',
                    'task_type': 'hearing_prep',
                    'priority': 'high',
                }
            ]
        }
        
        return task_templates.get(stage, [])
    
    def _build_case_analysis_prompt(
        self,
        case: Dict[str, Any],
        events: List[Dict[str, Any]],
        documents: List[Dict[str, Any]],
        notes: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for AI case analysis."""
        return f"""
Analyze this Kenyan legal case and provide a comprehensive assessment:

**Case Details:**
- Case Number: {case.get('case_number', 'Not set')}
- Type: {case.get('case_type')}
- Court: {case.get('court_level')} - {case.get('court_location', '')}
- Status: {case.get('case_status')}
- Current Stage: {case.get('current_stage')}

**Parties:**
- Plaintiff/Petitioner: {case.get('plaintiff_petitioner', 'Not set')}
- Defendant/Respondent: {case.get('defendant_respondent', 'Not set')}

**Timeline ({len(events)} events):**
{self._format_events_for_prompt(events[:5])}

**Documents ({len(documents)} linked):**
{self._format_documents_for_prompt(documents[:5])}

**Legal Issues Noted:**
{self._format_notes_for_prompt(notes)}

Please provide:
1. Brief case summary (2-3 sentences)
2. Risk assessment with case strength (0-100%)
3. Key risks and opportunities
4. Strategic recommendations for proceeding

Format your response in clear sections.
"""
    
    def _format_events_for_prompt(self, events: List[Dict[str, Any]]) -> str:
        """Format events for AI prompt."""
        if not events:
            return "No events recorded yet"
        
        return "\n".join([
            f"- {event.get('event_date')}: {event.get('event_title')} ({event.get('event_type')})"
            for event in events
        ])
    
    def _format_documents_for_prompt(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents for AI prompt."""
        if not documents:
            return "No documents linked yet"
        
        return "\n".join([
            f"- {doc.get('document_type')}: {doc.get('filing_date', 'Not filed')}"
            for doc in documents
        ])
    
    def _format_notes_for_prompt(self, notes: List[Dict[str, Any]]) -> str:
        """Format notes for AI prompt."""
        if not notes:
            return "No legal issues noted"
        
        return "\n".join([f"- {note.get('note_text')}" for note in notes[:3]])
    
    def _parse_ai_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse AI response into structured data."""
        # Simple parsing - could be enhanced with more sophisticated NLP
        lines = analysis_text.split('\n')
        
        result = {
            'summary': '',
            'risk_assessment': {'strength': None, 'risks': [], 'opportunities': []},
            'strategies': []
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            if 'summary' in line.lower():
                current_section = 'summary'
            elif 'risk' in line.lower() or 'strength' in line.lower():
                current_section = 'risk'
            elif 'strateg' in line.lower() or 'recommend' in line.lower():
                current_section = 'strategy'
            elif current_section == 'summary' and not line.startswith('#'):
                result['summary'] += line + ' '
            elif current_section == 'strategy' and line.startswith('-'):
                result['strategies'].append(line[1:].strip())
            elif current_section == 'risk' and '%' in line:
                # Extract percentage
                import re
                match = re.search(r'(\d+)%', line)
                if match:
                    result['risk_assessment']['strength'] = int(match.group(1))
        
        result['summary'] = result['summary'].strip()
        return result
