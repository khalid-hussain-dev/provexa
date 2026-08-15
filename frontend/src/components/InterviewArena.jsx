import { useEffect, useState } from 'react';
import { ArrowRight, CheckCircle2, MessageSquare, Send } from 'lucide-react';
import { answerInterview, completeInterview, createInterview } from '../services/api';
import { ErrorState, LoadingState, Notice, StepHeader } from './UI';

export default function InterviewArena({ candidate, selectedJob, onComplete }) {
  const [interview, setInterview] = useState(null);
  const [answer, setAnswer] = useState('');
  const [confidence, setConfidence] = useState(5);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [recorded, setRecorded] = useState(false);

  useEffect(() => {
    if (selectedJob?.job_id) startInterview();
  }, [selectedJob?.job_id]);

  async function startInterview() {
    setLoading(true);
    setError('');
    setInterview(null);
    try {
      const created = await createInterview({ jobId: selectedJob.job_id, numQuestions: 3 });
      setInterview({ ...created, currentQuestion: created.first_question, answered: 0 });
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitAnswer(event) {
    event.preventDefault();
    if (!answer.trim() || !interview?.currentQuestion) return;
    setSubmitting(true);
    setError('');
    try {
      const result = await answerInterview({ interviewId: interview.interview_id, questionId: interview.currentQuestion.question_id, answer: answer.trim(), confidence });
      setInterview((current) => ({ ...current, currentQuestion: result.next_question, answered: current.answered + 1 }));
      setAnswer('');
      setRecorded(true);
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function finishInterview() {
    setSubmitting(true);
    setError('');
    try {
      const result = await completeInterview(interview.interview_id);
      onComplete({ interviewId: interview.interview_id, evaluation: result });
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (!selectedJob) return <div className="workspace-page"><StepHeader eyebrow="03 · Interview" title="Select a target job first." description="The interview is generated from the owned job and profile context." /><Notice tone="neutral">Return to Target job and select an opportunity.</Notice></div>;
  if (loading) return <LoadingState title="Preparing the assessment" message={`Creating a persisted interview for ${selectedJob.title}…`} />;
  if (error && !interview) return <div className="workspace-page"><ErrorState message={error} onRetry={startInterview} /></div>;
  if (!interview) return <div className="workspace-page"><ErrorState title="Interview session unavailable" message="The host did not return an interview session. No answers were submitted." onRetry={startInterview} /></div>;

  const question = interview.currentQuestion;
  const finished = !question;
  return <div className="workspace-page narrow-page"><StepHeader eyebrow="03 · Interview" title="Show the evidence under pressure." description={`${selectedJob.title} · ${selectedJob.company}. Answers are recorded against this authenticated interview.`}><div className="assessment-count">{interview.answered} / {interview.total_questions || 3}</div></StepHeader>{error && <ErrorState message={error} onRetry={() => setError('')} />}{recorded && <Notice tone="success"><CheckCircle2 size={16} /> Answer recorded. Continue when ready.</Notice>}<section className="assessment-surface"><div className="assessment-meta"><span>PROVEXA assessment</span><span>Candidate: {candidate.name}</span></div>{finished ? <div className="assessment-complete"><CheckCircle2 size={42} /><h2>All answers recorded.</h2><p>The integrated evaluator is ready to produce the interview result.</p><button type="button" className="btn-primary" onClick={finishInterview} disabled={submitting}>{submitting ? 'Compiling verdict…' : 'View interview verdict'} <ArrowRight size={16} /></button></div> : <><div className="question-label">Question {interview.answered + 1}</div><h2>{question.question}</h2><div className="question-tags"><span>{question.category || question.competency}</span><span>{question.difficulty || 'assessment'}</span></div><form onSubmit={submitAnswer}><label className="form-label" htmlFor="interview-answer">Your response</label><textarea id="interview-answer" className="form-textarea" rows="8" value={answer} onChange={(event) => { setAnswer(event.target.value); setRecorded(false); }} placeholder="Use concrete evidence, decisions, outcomes, and trade-offs…" required /><div className="answer-footer"><label className="confidence-control" htmlFor="answer-confidence">Confidence <strong>{confidence}/10</strong><input id="answer-confidence" type="range" min="1" max="10" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} /></label><button type="submit" className="btn-primary" disabled={submitting || !answer.trim()}>{submitting ? 'Recording…' : 'Record answer'} <Send size={15} /></button></div></form></>}</section><div className="assessment-note"><MessageSquare size={15} /> The adapter stores the transcript; the Intelligence workflow owns evaluation semantics.</div></div>;
}
