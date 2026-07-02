import React, { useState, useEffect } from 'react';
import { candidateService, schedulerService, jobService } from '../services/api';
import { Candidate, Interview, JobDescription } from '../types';
import { 
  Users, Calendar, CheckCircle2, XCircle, 
  ArrowUpRight, Plus, Loader, Sparkles
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [candsData, intsData, jobsData] = await Promise.all([
          candidateService.list(),
          schedulerService.listInterviews(),
          jobService.list()
        ]);
        setCandidates(candsData);
        setInterviews(intsData);
        setJobs(jobsData);
      } catch (err) {
        console.error('Error fetching dashboard details:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalCandidates = candidates.length;
  const interviewsCount = interviews.length;
  const shortlistedCount = candidates.filter(c => c.status === 'Shortlisted').length;
  const rejectedCount = candidates.filter(c => c.status === 'Rejected').length;
  
  // Calculate average ATS score
  const candidatesWithScores = candidates.filter(c => c.ats_score !== undefined);
  const avgScore = candidatesWithScores.length 
    ? Math.round(candidatesWithScores.reduce((acc, c) => acc + (c.ats_score || 0), 0) / candidatesWithScores.length)
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader className="w-10 h-10 animate-spin text-brand-600" />
      </div>
    );
  }

  const stats = [
    { label: 'Total Candidates', value: totalCandidates, icon: Users, color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/30 dark:text-blue-400' },
    { label: 'Interviews Scheduled', value: interviewsCount, icon: Calendar, color: 'text-amber-600 bg-amber-50 dark:bg-amber-950/30 dark:text-amber-400' },
    { label: 'Shortlisted Candidates', value: shortlistedCount, icon: CheckCircle2, color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30 dark:text-emerald-400' },
    { label: 'Rejected Candidates', value: rejectedCount, icon: XCircle, color: 'text-rose-600 bg-rose-50 dark:bg-rose-950/30 dark:text-rose-400' },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-outfit font-bold text-3xl text-slate-900 dark:text-white">Recruitment Workspace</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Review candidates matching pipelines and schedule hiring sessions.</p>
        </div>
        <Link
          to="/jobs"
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-brand-500/10 active:scale-[0.98] transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Post New Job</span>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                  {stat.label}
                </span>
                <span className="font-outfit font-bold text-3xl mt-2 block text-slate-900 dark:text-white">
                  {stat.value}
                </span>
              </div>
              <div className={`p-4 rounded-xl ${stat.color}`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Analytics Highlights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Recruitment Pipeline Chart-alike */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60 pb-4">
            <h3 className="font-outfit font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-brand-500" />
              <span>Pipeline Health & Analytics</span>
            </h3>
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 dark:text-indigo-400 px-3 py-1 rounded-full">
              Avg ATS: {avgScore}%
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-slate-50 dark:bg-slate-950/40 rounded-2xl">
              <span className="text-xs text-slate-400 block mb-1">Pass Ratio</span>
              <span className="font-outfit font-bold text-2xl text-slate-900 dark:text-white">
                {totalCandidates ? Math.round((shortlistedCount / totalCandidates) * 100) : 0}%
              </span>
            </div>
            <div className="p-4 bg-slate-50 dark:bg-slate-950/40 rounded-2xl">
              <span className="text-xs text-slate-400 block mb-1">Rejection Rate</span>
              <span className="font-outfit font-bold text-2xl text-slate-900 dark:text-white">
                {totalCandidates ? Math.round((rejectedCount / totalCandidates) * 100) : 0}%
              </span>
            </div>
            <div className="p-4 bg-slate-50 dark:bg-slate-950/40 rounded-2xl">
              <span className="text-xs text-slate-400 block mb-1">Shortlist Confidence</span>
              <span className="font-outfit font-bold text-2xl text-slate-900 dark:text-white">
                High
              </span>
            </div>
          </div>

          {/* Simple Visual Breakdown of matching pipeline */}
          <div className="space-y-4 pt-2">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Candidate Quality Breakdown</h4>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1 text-slate-500">
                  <span>Elite Matches (&gt;85% ATS)</span>
                  <span>{candidates.filter(c => (c.ats_score || 0) >= 85).length} candidates</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                  <div 
                    className="bg-brand-500 h-2 rounded-full transition-all duration-500" 
                    style={{ width: `${totalCandidates ? (candidates.filter(c => (c.ats_score || 0) >= 85).length / totalCandidates) * 100 : 0}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1 text-slate-500">
                  <span>Consider Matches (50%-84% ATS)</span>
                  <span>{candidates.filter(c => (c.ats_score || 0) >= 50 && (c.ats_score || 0) < 85).length} candidates</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                  <div 
                    className="bg-indigo-500 h-2 rounded-full transition-all duration-500" 
                    style={{ width: `${totalCandidates ? (candidates.filter(c => (c.ats_score || 0) >= 50 && (c.ats_score || 0) < 85).length / totalCandidates) * 100 : 0}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Active Job Roles List */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60 pb-4 mb-4">
            <h3 className="font-outfit font-bold text-lg text-slate-900 dark:text-white">Active Roles</h3>
            <span className="text-xs text-slate-400 font-semibold">{jobs.length} Job Openings</span>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto max-h-[220px] pr-1">
            {jobs.map((job) => (
              <Link 
                key={job.id} 
                to="/candidates" 
                className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
              >
                <div>
                  <h4 className="text-sm font-semibold text-slate-800 dark:text-white leading-snug">{job.title}</h4>
                  <span className="text-xs text-slate-400 mt-1 block">Exp required: {job.experience_years} years</span>
                </div>
                <div className="w-7 h-7 rounded-full bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 flex items-center justify-center">
                  <ArrowUpRight className="w-4 h-4" />
                </div>
              </Link>
            ))}
            {!jobs.length && (
              <div className="text-center py-6 text-slate-400 text-sm">No job positions seeded yet.</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Applications Table */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60 pb-4 mb-6">
          <h3 className="font-outfit font-bold text-lg text-slate-900 dark:text-white">Recent Candidate Applications</h3>
          <Link to="/candidates" className="text-sm font-semibold text-brand-600 dark:text-brand-400 hover:underline">
            View All Candidates
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 dark:border-slate-800 text-xs font-bold text-slate-400 uppercase tracking-wider">
                <th className="pb-3 pl-4">Name</th>
                <th className="pb-3">Skills</th>
                <th className="pb-3">ATS Score</th>
                <th className="pb-3">Decision</th>
                <th className="pb-3 pr-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-sm">
              {candidates.slice(0, 5).map((cand) => (
                <tr key={cand.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20">
                  <td className="py-4 pl-4 font-semibold text-slate-900 dark:text-white">
                    {cand.name}
                    <span className="text-xs text-slate-400 block font-normal mt-0.5">{cand.email}</span>
                  </td>
                  <td className="py-4 max-w-[200px] truncate">
                    <div className="flex flex-wrap gap-1">
                      {cand.skills.slice(0, 3).map((s, i) => (
                        <span key={i} className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-600 dark:text-slate-300">
                          {s}
                        </span>
                      ))}
                      {cand.skills.length > 3 && (
                        <span className="text-xs text-slate-400">+{cand.skills.length - 3} more</span>
                      )}
                    </div>
                  </td>
                  <td className="py-4 font-bold text-slate-700 dark:text-slate-300">
                    {cand.ats_score !== undefined ? `${cand.ats_score}%` : 'TBD'}
                  </td>
                  <td className="py-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                      cand.match_details?.recommendation === 'Hire'
                        ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400'
                        : cand.match_details?.recommendation === 'Consider'
                        ? 'bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-brand-400'
                        : 'bg-rose-50 dark:bg-rose-950/30 text-rose-600 dark:text-rose-400'
                    }`}>
                      {cand.match_details?.recommendation || 'Evaluating'}
                    </span>
                  </td>
                  <td className="py-4 pr-4 text-right">
                    <span className={`text-xs px-2.5 py-1 rounded-lg font-bold uppercase ${
                      cand.status === 'Shortlisted'
                        ? 'bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-400'
                        : cand.status === 'Rejected'
                        ? 'bg-rose-100 dark:bg-rose-950/40 text-rose-800 dark:text-rose-400'
                        : cand.status === 'Hired'
                        ? 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-400'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                    }`}>
                      {cand.status}
                    </span>
                  </td>
                </tr>
              ))}
              {!candidates.length && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    No recent applications. Go to **Candidates** to upload a resume.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
