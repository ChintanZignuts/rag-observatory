from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import EvaluationResult, EvaluationRun, QuestionSetItem


class ApiEndpointTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token

        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_health_check(self):
        response = self.client.get('/api/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_ask_requires_question(self):
        response = self.client.post('/api/ask/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'question is required'})

    @patch('api.views.answer_question')
    def test_ask_returns_rag_answer(self, mocked_answer_question):
        mocked_answer_question.return_value = {
            'id': 1,
            'question': 'What is the resignation notice period?',
            'answer': 'The resignation notice period is listed in the resignation policy.',
            'sources': [],
            'retrieved_context': [],
            'latency_ms': 25,
            'prompt_tokens': 100,
            'completion_tokens': 20,
        }

        response = self.client.post(
            '/api/ask/',
            {'question': 'What is the resignation notice period?', 'top_k': 3},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['answer'], 'The resignation notice period is listed in the resignation policy.')
        mocked_answer_question.assert_called_once_with(
            question='What is the resignation notice period?',
            top_k=3,
            min_similarity=None,
        )

    def test_evaluation_runs_list(self):
        EvaluationRun.objects.create(name='Baseline', status='completed')

        response = self.client.get('/api/evaluation-runs/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['name'], 'Baseline')

    def test_evaluation_run_detail(self):
        question = QuestionSetItem.objects.create(
            question_id='HR-01',
            category='Leave',
            difficulty='easy',
            question='How many casual leaves are allowed?',
        )
        evaluation_run = EvaluationRun.objects.create(name='Baseline', status='completed')
        EvaluationResult.objects.create(
            evaluation_run=evaluation_run,
            question_item=question,
            generated_answer='Employees are allowed casual leave as defined in policy.',
        )

        response = self.client.get(f'/api/evaluation-runs/{evaluation_run.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Baseline')
        self.assertEqual(response.json()['results'][0]['question_id'], 'HR-01')

    @patch('api.management.commands.run_eval.score_evaluation_result')
    @patch('api.management.commands.run_eval.answer_question')
    def test_run_eval_can_save_ragas_scores(self, mocked_answer_question, mocked_score):
        from django.core.management import call_command

        QuestionSetItem.objects.create(
            question_id='HR-01',
            category='Leave',
            difficulty='easy',
            question='How many casual leaves are allowed?',
            expected_answer='The policy defines leave in the leave policy.',
        )
        mocked_answer_question.return_value = {
            'id': None,
            'answer': 'The policy defines leave in the leave policy.',
            'retrieved_context': [{'text': 'Leave policy context'}],
        }
        mocked_score.return_value = {
            'context_precision': 0.9,
            'faithfulness': 0.8,
            'answer_relevance': 0.7,
        }

        call_command('run_eval', '--name', 'Scored', '--limit', '1', '--score-with-ragas')

        result = EvaluationResult.objects.get()
        evaluation_run = EvaluationRun.objects.get(name='Scored')
        self.assertEqual(result.context_precision, 0.9)
        self.assertEqual(result.faithfulness, 0.8)
        self.assertEqual(result.answer_relevance, 0.7)
        self.assertEqual(evaluation_run.average_context_precision, 0.9)

    @patch('api.views.answer_question')
    def test_ask_returns_rag_answer_with_similarity(self, mocked_answer_question):
        mocked_answer_question.return_value = {
            'id': 1,
            'question': 'notice period?',
            'answer': '30 days',
            'sources': [],
            'retrieved_context': [],
            'latency_ms': 25,
            'prompt_tokens': 100,
            'completion_tokens': 20,
        }

        response = self.client.post(
            '/api/ask/',
            {
                'question': 'notice period?',
                'top_k': 3,
                'min_similarity': 0.75,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        mocked_answer_question.assert_called_once_with(
            question='notice period?',
            top_k=3,
            min_similarity=0.75,
        )

    @patch('api.views.langfuse_client')
    @patch('api.views.answer_question')
    @override_settings(LANGFUSE_PUBLIC_KEY='pk-lf-abc-123', LANGFUSE_HOST='https://eu.cloud.langfuse.com')
    def test_ask_returns_langfuse_project_id(self, mocked_answer_question, mocked_langfuse_client):
        mocked_answer_question.return_value = {
            'id': 1,
            'question': 'test question',
            'answer': 'test answer',
            'sources': [],
            'retrieved_context': [],
            'latency_ms': 25,
            'prompt_tokens': 100,
            'completion_tokens': 20,
        }
        mocked_langfuse_client._get_project_id.return_value = 'cmqt-project-id'

        response = self.client.post(
            '/api/ask/',
            {'question': 'test question'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['langfuse_project_id'], 'cmqt-project-id')
        self.assertEqual(response.json()['langfuse_host'], 'https://eu.cloud.langfuse.com')

    @patch('api.views.langfuse_client', None)
    @patch('api.views.answer_question')
    @override_settings(LANGFUSE_PUBLIC_KEY='pk-lf-fallback-uuid', LANGFUSE_HOST='https://eu.cloud.langfuse.com')
    def test_ask_returns_langfuse_project_id_fallback(self, mocked_answer_question):
        mocked_answer_question.return_value = {
            'id': 1,
            'question': 'test question',
            'answer': 'test answer',
            'sources': [],
            'retrieved_context': [],
            'latency_ms': 25,
            'prompt_tokens': 100,
            'completion_tokens': 20,
        }

        response = self.client.post(
            '/api/ask/',
            {'question': 'test question'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['langfuse_project_id'], 'fallback-uuid')
        self.assertEqual(response.json()['langfuse_host'], 'https://eu.cloud.langfuse.com')

    @patch('api.views.threading.Thread')
    def test_run_evaluation_endpoint(self, mocked_thread):
        response = self.client.post(
            '/api/evaluation-runs/run/',
            {'name': 'Test API Run', 'score_with_ragas': False},
            format='json',
        )

        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Test API Run')
        self.assertEqual(data['status'], 'running')

        run = EvaluationRun.objects.get(id=data['id'])
        self.assertEqual(run.name, 'Test API Run')
        self.assertEqual(run.status, 'running')
        mocked_thread.assert_called_once()

    def test_unauthenticated_request_fails(self):
        client = APIClient()
        response = client.get('/api/overview/')
        self.assertEqual(response.status_code, 401)
