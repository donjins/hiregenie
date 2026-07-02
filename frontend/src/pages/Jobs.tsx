import React, { useState, useEffect } from 'react';
import { jobService } from '../services/api';
import { JobDescription } from '../types';
import { Briefcase, Trash2, Loader, Check, XCircle } from 'lucide-react';

export const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [requirements, setRequirements] = useState('');
  const [expYears, setExpYears] = useState(2);
  const [eduReq, setEduReq] = useState("Bachelor's Degree");
  
  // UI messages
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const data = await jobService.list();
        setJobs(data);
      } catch (err) {
        setError('Failed to fetch job descriptions.');
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess('');
    setError('');
    
    try {
      const payload = {
        title,
        description,
        requirements,
        experience_years: expYears,
        education_requirements: eduReq
      };
      
      const newJob = await jobService.create(payload);
      setJobs(prev => [newJob, ...prev]);
      setSuccess(`Job position "${title}" posted successfully!`);
      
      // Reset Form
      setTitle('');
      setDescription('');
      setRequirements('');
      setExpYears(2);
      setEduReq("Bachelor's Degree");
      setShowForm(false);
    } catch (err) {
      setError('Failed to create job description.');
    }
  };

  const handleDelete = async (jobId: string, jobTitle: string) => {
    if (!window.confirm(`Are you sure you want to delete the job: ${jobTitle}?`)) return;
    
    try {
      await jobService.delete(jobId);
      setJobs(prev => prev.filter(j => j.id !== jobId));
      setSuccess(`Job "${jobTitle}" deleted successfully.`);
    } catch (err) {
      setError('Failed to delete job description.');
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-outfit font-bold text-3xl text-slate-900 dark:text-white">Active Job Roles</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Manage positions, define experience parameters, and query matching criteria.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md active:scale-[0.98] transition-all"
        >
          {showForm ? 'Cancel Creation' : 'Create Job Profile'}
        </button>
      </div>

      {/* Messages */}
      {success && (
        <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 text-emerald-600 dark:text-emerald-400 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
          <Check className="w-4 h-4 shrink-0" />
          <span>{success}</span>
        </div>
      )}
      {error && (
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
          <XCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Form Panel */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm space-y-6">
          <h3 className="font-outfit font-bold text-base text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800/60 pb-3">
            New Job Description Parameters
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Job Title
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Senior Python Developer"
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Min Exp (Years)
                </label>
                <input
                  type="number"
                  required
                  min="0"
                  max="15"
                  value={expYears}
                  onChange={(e) => setExpYears(parseInt(e.target.value))}
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Education Requirements
                </label>
                <select
                  value={eduReq}
                  onChange={(e) => setEduReq(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm font-semibold"
                >
                  <option value="Bachelor's Degree">Bachelor's Degree</option>
                  <option value="Master's Degree">Master's Degree</option>
                  <option value="Ph.D.">Ph.D.</option>
                  <option value="No Degree Required">No Degree Required</option>
                </select>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Job Description
              </label>
              <textarea
                required
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief summary of duties and responsibilities..."
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Required Technical Keywords (comma separated)
              </label>
              <textarea
                required
                rows={4}
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="e.g. Python, Django, SQL, AWS, Docker"
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white rounded-xl text-sm font-semibold active:scale-[0.98] transition-all shadow-md shadow-brand-500/10"
          >
            Post Position to Database
          </button>
        </form>
      )}

      {/* Roles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="flex items-center justify-center col-span-full py-20">
            <Loader className="w-8 h-8 animate-spin text-brand-600" />
          </div>
        ) : (
          jobs.map((job) => (
            <div key={job.id} className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm flex flex-col justify-between hover:shadow-md hover:border-brand-200 transition-all">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-brand-50 dark:bg-brand-950/20 text-brand-600 dark:text-brand-400 rounded-xl">
                    <Briefcase className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-outfit font-bold text-base text-slate-800 dark:text-white leading-tight">
                      {job.title}
                    </h3>
                    <span className="text-[10px] text-slate-400 mt-1 block">Created at: {new Date(job.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed line-clamp-3">
                  {job.description}
                </p>

                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Tech Criteria</span>
                  <div className="flex flex-wrap gap-1">
                    {job.requirements.split(',').map((req, idx) => (
                      <span key={idx} className="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-600 dark:text-slate-300 font-medium">
                        {req.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800/60 pt-4 mt-6">
                <div className="text-xs text-slate-400">
                  Target Exp: <strong className="text-slate-600 dark:text-slate-200 font-semibold">{job.experience_years}+ yrs</strong>
                </div>
                
                <button
                  onClick={() => handleDelete(job.id, job.title)}
                  className="p-2 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/20 hover:text-rose-700 transition-colors"
                  title="Delete Job Role"
                >
                  <Trash2 className="w-4.5 h-4.5" />
                </button>
              </div>
            </div>
          ))
        )}

        {!loading && !jobs.length && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/40 p-12 rounded-2xl text-center text-slate-400 text-sm col-span-full">
            No active job openings created. Use the form above to post one.
          </div>
        )}
      </div>
    </div>
  );
};
