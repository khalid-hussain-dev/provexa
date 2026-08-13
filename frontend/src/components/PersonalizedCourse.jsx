import { useEffect, useState } from 'react';
import { ArrowRight, CheckCircle2, Code2, GraduationCap } from 'lucide-react';
import { generateCourse, updateCourseProgress } from '../services/api';
import { ErrorState, EmptyState, LoadingState, Notice, ProgressBar, StepHeader } from './UI';

export default function PersonalizedCourse({ interviewState, course, onCourseReady, onTailorResume }) {
  const [loading, setLoading] = useState(!course);
  const [error, setError] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const [completed, setCompleted] = useState([]);
  const [answer, setAnswer] = useState('');
  const [saving, setSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState('');

  useEffect(() => {
    if (!course && interviewState?.interviewId) loadCourse();
  }, [course, interviewState?.interviewId]);

  async function loadCourse() {
    setLoading(true);
    setError('');
    try {
      onCourseReady(await generateCourse(interviewState.interviewId));
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setLoading(false);
    }
  }

  async function completeModule(event) {
    event.preventDefault();
    const module = course?.modules?.[activeIndex];
    if (!module || !answer.trim()) return;
    setSaving(true);
    setError('');
    try {
      await updateCourseProgress({ courseId: course.course_id, moduleId: module.module_id, completionPercent: 100, assessmentScore: 100 });
      setCompleted((current) => current.includes(module.module_id) ? current : [...current, module.module_id]);
      setSavedMessage('Progress saved to the authenticated candidate course.');
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState title="Generating the readiness path" message="The integrated learning adapter is mapping the completed interview into modules…" />;
  if (error && !course) return <div className="workspace-page"><ErrorState message={error} onRetry={loadCourse} /></div>;
  if (!course) return <div className="workspace-page"><StepHeader eyebrow="05 · Learning" title="Complete the interview first." description="Course generation requires a completed owned interview." /><EmptyState title="No course yet" message="Return to Readiness and generate the learning path." /></div>;

  const module = course.modules?.[activeIndex];
  const progress = course.modules?.length ? Math.round((completed.length / course.modules.length) * 100) : 0;
  return <div className="workspace-page"><StepHeader eyebrow="05 · Learning" title={course.title} description={`${course.target_role || 'Target role'} · ${course.modules?.length || 0} modules`}><div className="step-count"><GraduationCap size={16} /> {progress}% complete</div></StepHeader>{error && <ErrorState message={error} onRetry={() => setError('')} />}{savedMessage && <Notice tone="success"><CheckCircle2 size={16} /> {savedMessage}</Notice>}<div className="course-layout"><aside className="surface course-nav"><ProgressBar value={progress} label="Readiness path" /><div className="module-list">{course.modules.map((item, index) => <button type="button" key={item.module_id} className={index === activeIndex ? 'active' : ''} onClick={() => { setActiveIndex(index); setAnswer(''); setSavedMessage(''); }}><span>0{index + 1}</span><span>{item.content?.skill_name || item.title}</span>{completed.includes(item.module_id) && <CheckCircle2 size={15} />}</button>)}</div></aside><section className="surface module-content">{module ? <><span className="eyebrow">Module 0{activeIndex + 1} · {module.content?.skill_name || 'Capability'}</span><h2>{module.title}</h2><p>{module.objective}</p>{module.content?.code_example && <div className="code-block"><div className="code-label"><Code2 size={14} /> Reference</div><pre>{module.content.code_example}</pre></div>}<div className="challenge-block"><span className="eyebrow">Practical challenge</span><h3>{module.challenge?.validation_exercise || 'Apply the concept to your target role.'}</h3><form onSubmit={completeModule}><textarea className="form-textarea mono-input" rows="5" value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Describe or paste your solution…" required /><button type="submit" className="btn-primary" disabled={saving || completed.includes(module.module_id)}>{completed.includes(module.module_id) ? 'Module completed' : saving ? 'Saving progress…' : 'Complete module'} <CheckCircle2 size={15} /></button></form></div></> : <EmptyState title="No modules returned" message="The course response did not contain any modules." />}<div className="form-actions"><button type="button" className="btn-primary" onClick={onTailorResume} disabled={!completed.length}><span>Continue to resume builder</span><ArrowRight size={16} /></button></div></section></div></div>;
}
