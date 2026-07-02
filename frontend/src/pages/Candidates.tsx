import React, { useState, useEffect, useRef } from 'react';
import { candidateService, jobService } from '../services/api';
import { Candidate, JobDescription } from '../types';
import { 
  Search, UploadCloud, ChevronRight, CheckCircle2, 
  XCircle, Award, Briefcase, GraduationCap, 
  Sparkles, ExternalLink, Loader, Check 
} from 'lucide-react';

export const Candidates: React.FC = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [semanticMode, setSemanticMode] = useState(false);
  const [rankingMode, setRankingMode] = useState(false);
  const [rankingData, setRankingData] = useState<any>(null);
  
  // Details Modal
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  
  // UI states
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch initial data
  useEffect(() => {
    const init = async () => {
      try {
        const jobsData = await jobService.list();
        setJobs(jobsData);
        if (jobsData.length > 0) {
          setSelectedJobId(jobsData[0].id);
        }
      } catch (err) {
        console.error('Error fetching jobs:', err);
      }
    };
    init();
  }, []);

  // Fetch candidates based on filters
  useEffect(() => {
    if (!selectedJobId) return;
    
    const fetchCandidates = async () => {
      setLoading(true);
      setError('');
      try {
        if (rankingMode) {
          // Ranking Mode fetching
          const rankRes = await candidateService.getRankings(selectedJobId);
          setRankingData(rankRes);
          
          // Re-fetch plain candidates to support full modal details
          const cands = await candidateService.list(selectedJobId);
          setCandidates(cands);
        } else if (semanticMode && searchQuery) {
          // Semantic search mode
          const searchRes = await candidateService.semanticSearch(searchQuery);
          // filter by selected job if present
          const cands = searchRes
            .map(r => r.candidate)
            .filter(c => c.job_id === selectedJobId);
          setCandidates(cands);
        } else {
          // Standard fetching (optional search filter)
          const cands = await candidateService.list(selectedJobId);
          if (searchQuery) {
            const query = searchQuery.toLowerCase();
            const filtered = cands.filter(c => 
              c.name.toLowerCase().includes(query) || 
              c.skills.some(s => s.toLowerCase().includes(query))
            );
            setCandidates(filtered);
          } else {
            setCandidates(cands);
          }
        }
      } catch (err) {
        setError('Failed to load candidate profiles.');
      } finally {
        setLoading(false);
      }
    };

    fetchCandidates();
  }, [selectedJobId, searchQuery, semanticMode, rankingMode]);

  // Handle Drag-and-Drop / Upload
  const handleFileUpload = async (file: File) => {
    if (!selectedJobId) {
      setError('Please select a Job Position before uploading.');
      return;
    }
    setUploading(true);
    setError('');
    setSuccessMsg('');
    try {
      const uploadRes = await candidateService.upload(selectedJobId, file);
      setSuccessMsg(uploadRes.message || 'Resume uploaded and parsed successfully!');
      
      // Refresh candidates list
      const cands = await candidateService.list(selectedJobId);
      setCandidates(cands);
      
      // Auto select newly uploaded candidate for details review
      setSelectedCandidate(uploadRes.candidate);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse the uploaded resume.');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  // Status updating
  const handleUpdateStatus = async (candId: string, nextStatus: 'Shortlisted' | 'Rejected' | 'Hired') => {
    try {
      await candidateService.updateStatus(candId, nextStatus);
      
      // Update local state
      setCandidates(prev => prev.map(c => c.id === candId ? { ...c, status: nextStatus } : c));
      if (selectedCandidate && selectedCandidate.id === candId) {
        setSelectedCandidate(prev => prev ? { ...prev, status: nextStatus } : null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-outfit font-bold text-3xl text-slate-900 dark:text-white">Candidates Directory</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Screen resumes, view automatic ATS compatibility, and run candidate ranking algorithms.</p>
        </div>
        
        {/* Job Selector */}
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Position:</span>
          <select
            value={selectedJobId}
            onChange={(e) => {
              setSelectedJobId(e.target.value);
              setRankingMode(false); // Reset ranking state when job changes
            }}
            className="px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-800 dark:text-slate-100 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm shadow-sm"
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>{j.title}</option>
            ))}
            {!jobs.length && <option value="">No Active Positions</option>}
          </select>
        </div>
      </div>

      {/* Main Grid: Upload left, candidate listing right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left column: Filters and Upload Panels */}
        <div className="space-y-6">
          
          {/* Upload panel */}
          <div 
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="bg-white dark:bg-slate-900 p-6 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800/80 shadow-sm flex flex-col items-center justify-center text-center cursor-pointer group hover:border-brand-500 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".pdf"
              onChange={(e) => e.target.files && handleFileUpload(e.target.files[0])}
            />
            {uploading ? (
              <div className="py-8 flex flex-col items-center gap-3">
                <Loader className="w-12 h-12 text-brand-600 animate-spin" />
                <span className="text-sm font-semibold text-slate-500 dark:text-slate-400 animate-pulse">
                  Agent parsing resume...
                </span>
              </div>
            ) : (
              <div className="py-6 flex flex-col items-center">
                <div className="w-16 h-16 rounded-2xl bg-brand-50 dark:bg-brand-950/20 text-brand-600 dark:text-brand-400 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform duration-200">
                  <UploadCloud className="w-8 h-8" />
                </div>
                <h3 className="font-outfit font-bold text-base text-slate-800 dark:text-white">Upload Candidate Resume</h3>
                <p className="text-xs text-slate-400 mt-2 max-w-[200px]">Drag & drop candidate resume PDF here, or click to browse files.</p>
                <span className="mt-4 text-xs font-bold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/40 px-3 py-1 rounded-full group-hover:bg-brand-100 transition-colors">
                  PDF format only
                </span>
              </div>
            )}
          </div>

          {/* Error and success messages */}
          {error && (
            <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 text-xs px-4 py-3 rounded-xl">
              {error}
            </div>
          )}
          {successMsg && (
            <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 text-emerald-600 dark:text-emerald-400 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
              <Check className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Search filters Panel */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm space-y-4">
            <h4 className="font-outfit font-bold text-sm text-slate-800 dark:text-white uppercase tracking-wider">Search & Filters</h4>
            
            {/* Input query */}
            <div className="relative">
              <input
                type="text"
                placeholder={semanticMode ? "Ask natural queries: 'python developer AWS'..." : "Search by candidate name or skill..."}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
              />
              <Search className="w-5 h-5 text-slate-400 absolute left-3 top-2.5" />
            </div>

            {/* Semantic Mode Toggle */}
            <button
              onClick={() => {
                setSemanticMode(!semanticMode);
                setRankingMode(false);
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-xs font-bold border transition-colors ${
                semanticMode
                  ? 'bg-brand-50 border-brand-300 text-brand-700 dark:bg-brand-950/30 dark:border-brand-900 dark:text-brand-400'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-400'
              }`}
            >
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-brand-500" />
                <span>AI Semantic Search (FAISS)</span>
              </div>
              <span className={`w-2 h-2 rounded-full ${semanticMode ? 'bg-brand-500 animate-pulse' : 'bg-slate-300'}`}></span>
            </button>

            {/* Candidate ranking algorithm */}
            <button
              onClick={() => {
                setRankingMode(!rankingMode);
                setSemanticMode(false);
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-xs font-bold border transition-colors ${
                rankingMode
                  ? 'bg-indigo-50 border-indigo-300 text-indigo-700 dark:bg-indigo-950/30 dark:border-indigo-900 dark:text-indigo-400'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-400'
              }`}
            >
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-indigo-500" />
                <span>AI Candidate Ranking Agent</span>
              </div>
              <span className={`w-2 h-2 rounded-full ${rankingMode ? 'bg-indigo-500 animate-pulse' : 'bg-slate-300'}`}></span>
            </button>
          </div>
        </div>

        {/* Right column: Candidate Profiles List */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Ranking header info */}
          {rankingMode && rankingData && (
            <div className="bg-indigo-50/50 dark:bg-indigo-950/10 p-5 rounded-2xl border border-indigo-200/50 dark:border-indigo-900/30">
              <div className="flex items-center justify-between border-b border-indigo-100 dark:border-indigo-900/40 pb-3 mb-3">
                <h4 className="font-outfit font-bold text-sm text-indigo-900 dark:text-indigo-400 uppercase tracking-wider">Ranking Analysis</h4>
                <span className="text-xs font-bold text-white bg-indigo-600 px-3 py-1 rounded-full">
                  Selection Confidence: {rankingData.selection_confidence_score}%
                </span>
              </div>
              <p className="text-xs text-indigo-800 dark:text-indigo-300 font-medium leading-relaxed">
                {rankingData.recruiter_recommendations}
              </p>
            </div>
          )}

          {/* List Wrapper */}
          <div className="space-y-4">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <Loader className="w-8 h-8 animate-spin text-brand-600" />
                <span className="text-sm text-slate-400">Querying candidates...</span>
              </div>
            ) : rankingMode && rankingData ? (
              // Ranked Candidate List
              rankingData.ranked_candidates.map((cand: any) => {
                // Find full candidate object for details Modal trigger
                const fullCandObj = candidates.find(c => c.id === cand.id);
                return (
                  <div 
                    key={cand.id} 
                    onClick={() => fullCandObj && setSelectedCandidate(fullCandObj)}
                    className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm flex items-center justify-between hover:shadow-md hover:border-brand-300 transition-all cursor-pointer"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 font-extrabold flex items-center justify-center text-sm">
                        #{cand.rank}
                      </div>
                      <div>
                        <h3 className="font-outfit font-bold text-base text-slate-800 dark:text-white">{cand.name}</h3>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {cand.key_skills.map((s: string, i: number) => (
                            <span key={i} className="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded font-medium text-slate-600 dark:text-slate-300">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <span className="text-xs text-slate-400 uppercase tracking-wider block">ATS Match</span>
                        <span className="font-outfit font-bold text-lg text-indigo-600 dark:text-indigo-400 mt-1 block">
                          {cand.match_percentage}%
                        </span>
                      </div>
                      <ChevronRight className="w-5 h-5 text-slate-400" />
                    </div>
                  </div>
                );
              })
            ) : (
              // Standard Candidate List
              candidates.map((cand) => (
                <div 
                  key={cand.id} 
                  onClick={() => setSelectedCandidate(cand)}
                  className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 hover:shadow-md hover:border-brand-300 transition-all cursor-pointer"
                >
                  <div className="space-y-2">
                    <div className="flex items-center gap-2.5">
                      <h3 className="font-outfit font-bold text-lg text-slate-800 dark:text-white leading-none">{cand.name}</h3>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
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
                    </div>
                    
                    <p className="text-xs text-slate-400">{cand.email} | {cand.phone}</p>
                    
                    <div className="flex flex-wrap gap-1 pt-1">
                      {cand.skills.slice(0, 5).map((s, i) => (
                        <span key={i} className="text-xs bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 rounded text-slate-600 dark:text-slate-300 font-medium">
                          {s}
                        </span>
                      ))}
                      {cand.skills.length > 5 && (
                        <span className="text-xs text-slate-400 font-medium px-2 py-0.5">+{cand.skills.length - 5} more</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-6 self-end md:self-auto">
                    <div className="text-right">
                      <span className="text-xs text-slate-400 uppercase tracking-wider block">ATS Score</span>
                      <span className="font-outfit font-bold text-xl text-brand-600 dark:text-brand-400 mt-1 block">
                        {cand.ats_score !== undefined ? `${cand.ats_score}%` : 'Evaluating'}
                      </span>
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-400" />
                  </div>
                </div>
              ))
            )}
            
            {!loading && !candidates.length && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/40 p-12 rounded-2xl text-center text-slate-400 text-sm">
                No candidates match the filter parameters. Please upload candidate resumes on the left to initialize.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Candidate Profile Details Drawer/Modal */}
      {selectedCandidate && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex justify-end transition-opacity duration-200">
          <div className="w-full max-w-3xl bg-white dark:bg-slate-900 h-full overflow-y-auto flex flex-col shadow-2xl animate-slide-in relative border-l border-slate-200/50 dark:border-slate-800/50">
            
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-100 dark:border-slate-800/60 flex items-center justify-between sticky top-0 bg-white dark:bg-slate-900 z-10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-brand-500 text-white font-bold flex items-center justify-center uppercase">
                  {selectedCandidate.name.slice(0, 2)}
                </div>
                <div>
                  <h2 className="font-outfit font-bold text-xl text-slate-900 dark:text-white leading-none">
                    {selectedCandidate.name}
                  </h2>
                  <span className="text-xs text-slate-400 mt-1.5 block">{selectedCandidate.email} | {selectedCandidate.phone}</span>
                </div>
              </div>
              
              <button 
                onClick={() => setSelectedCandidate(null)}
                className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-800 dark:hover:text-white flex items-center justify-center"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-8 flex-1">
              
              {/* Pipeline Decision Row */}
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-950/40 rounded-2xl">
                <div>
                  <span className="text-xs text-slate-400 font-semibold block uppercase">Recruiter Decision</span>
                  <div className="flex items-center gap-2 mt-1.5">
                    <button
                      onClick={() => handleUpdateStatus(selectedCandidate.id, 'Shortlisted')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        selectedCandidate.status === 'Shortlisted'
                          ? 'bg-amber-600 text-white'
                          : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      Shortlist
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(selectedCandidate.id, 'Hired')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        selectedCandidate.status === 'Hired'
                          ? 'bg-emerald-600 text-white'
                          : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      Hire
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(selectedCandidate.id, 'Rejected')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        selectedCandidate.status === 'Rejected'
                          ? 'bg-rose-600 text-white'
                          : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      Reject
                    </button>
                  </div>
                </div>
                
                <div className="text-right">
                  <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider block">ATS Match Score</span>
                  <span className="font-outfit font-extrabold text-2xl text-brand-600 dark:text-brand-400 mt-1 block">
                    {selectedCandidate.ats_score !== undefined ? `${selectedCandidate.ats_score}%` : 'TBD'}
                  </span>
                </div>
              </div>

              {/* Strengths & Weaknesses (AI Analysis) */}
              {selectedCandidate.match_details && (
                <div className="space-y-4">
                  <h3 className="font-outfit font-bold text-sm text-slate-800 dark:text-white uppercase tracking-wider flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-brand-500" />
                    <span>AI Match Analysis & Summary</span>
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-300 italic bg-brand-50/20 dark:bg-brand-950/10 p-4 rounded-xl border border-brand-100/50 dark:border-brand-900/30">
                    "{selectedCandidate.match_details.summary}"
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Strengths */}
                    <div className="p-4 bg-emerald-50/30 dark:bg-emerald-950/10 border border-emerald-200/50 dark:border-emerald-900/30 rounded-xl space-y-2">
                      <span className="text-xs font-bold text-emerald-800 dark:text-emerald-400 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" /> STRENGTHS
                      </span>
                      <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1.5 list-disc pl-4">
                        {selectedCandidate.match_details.strengths.map((str, idx) => (
                          <li key={idx}>{str}</li>
                        ))}
                      </ul>
                    </div>
                    {/* Weaknesses */}
                    <div className="p-4 bg-rose-50/30 dark:bg-rose-950/10 border border-rose-200/50 dark:border-rose-900/30 rounded-xl space-y-2">
                      <span className="text-xs font-bold text-rose-800 dark:text-rose-400 flex items-center gap-1.5">
                        <XCircle className="w-4 h-4 text-rose-500" /> AREAS OF CONCERN
                      </span>
                      <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1.5 list-disc pl-4">
                        {selectedCandidate.match_details.weaknesses.map((wk, idx) => (
                          <li key={idx}>{wk}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Skills Analysis */}
              <div className="space-y-4">
                <h3 className="font-outfit font-bold text-sm text-slate-800 dark:text-white uppercase tracking-wider">Candidate Skills</h3>
                <div className="flex flex-wrap gap-1.5">
                  {selectedCandidate.skills.map((skill, idx) => (
                    <span key={idx} className="text-xs bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-lg text-slate-700 dark:text-slate-200 font-semibold">
                      {skill}
                    </span>
                  ))}
                </div>
                
                {/* Missing Skills & Recommendations */}
                {selectedCandidate.match_details && selectedCandidate.match_details.missing_skills.length > 0 && (
                  <div className="mt-3 p-4 bg-slate-50 dark:bg-slate-950/40 rounded-xl space-y-2">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Missing Skills Gaps</span>
                    <div className="flex flex-wrap gap-1">
                      {selectedCandidate.match_details.missing_skills.map((s, i) => (
                        <span key={i} className="text-[10px] bg-red-100/50 dark:bg-red-950/30 text-red-700 dark:text-red-400 px-2 py-0.5 rounded font-bold">
                          {s}
                        </span>
                      ))}
                    </div>
                    {/* Learning Resources */}
                    {selectedCandidate.match_details.learning_resources.length > 0 && (
                      <div className="pt-2">
                        <span className="text-xs font-bold text-slate-400 block mb-1">Recommended Learning Paths:</span>
                        <div className="space-y-1.5">
                          {selectedCandidate.match_details.learning_resources.map((res, i) => (
                            <a 
                              key={i} 
                              href={res.url} 
                              target="_blank" 
                              rel="noreferrer" 
                              className="text-xs text-brand-600 dark:text-brand-400 font-semibold hover:underline flex items-center gap-1"
                            >
                              <span>{res.resource_name} (Skill: {res.skill})</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Experience list */}
              <div className="space-y-4">
                <h3 className="font-outfit font-bold text-sm text-slate-800 dark:text-white uppercase tracking-wider flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-slate-400" />
                  <span>Work Experience</span>
                </h3>
                <div className="space-y-4 relative border-l border-slate-100 dark:border-slate-800/80 pl-4 ml-2">
                  {selectedCandidate.experience.map((exp, idx) => (
                    <div key={idx} className="relative space-y-1">
                      <div className="w-3 h-3 rounded-full bg-slate-300 dark:bg-slate-700 absolute -left-[22px] top-1"></div>
                      <h4 className="text-sm font-semibold text-slate-800 dark:text-white">{exp.role}</h4>
                      <span className="text-xs text-slate-400 block">{exp.duration}</span>
                      <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mt-1">{exp.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Education */}
              <div className="space-y-4">
                <h3 className="font-outfit font-bold text-sm text-slate-800 dark:text-white uppercase tracking-wider flex items-center gap-2">
                  <GraduationCap className="w-5 h-5 text-slate-400" />
                  <span>Education</span>
                </h3>
                <div className="space-y-3">
                  {selectedCandidate.education.map((edu, idx) => (
                    <div key={idx} className="text-xs">
                      <h4 className="font-semibold text-slate-800 dark:text-white">{edu.degree}</h4>
                      <span className="text-slate-400 mt-0.5 block">{edu.institution}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Generated Interview Questions */}
              {selectedCandidate.generated_questions && (
                <div className="space-y-4 border-t border-slate-100 dark:border-slate-800/60 pt-6">
                  <h3 className="font-outfit font-bold text-sm text-slate-800 dark:text-white uppercase tracking-wider flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-brand-500" />
                    <span>AI Generated Interview Questions</span>
                  </h3>
                  
                  <div className="space-y-4">
                    {/* HR */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wide">HR Behavioral Questions</h4>
                      <div className="space-y-2">
                        {selectedCandidate.generated_questions.hr_questions.map((q, i) => (
                          <div key={i} className="p-3 bg-slate-50 dark:bg-slate-950/20 border border-slate-200/50 dark:border-slate-800/40 rounded-xl text-xs">
                            <p className="font-semibold text-slate-800 dark:text-white">Q: {q.question}</p>
                            <p className="text-slate-400 mt-1 italic">Evaluation Intent: {q.intent}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Technical */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wide">Technical Evaluation Tiers</h4>
                      <div className="space-y-3">
                        {Object.entries(selectedCandidate.generated_questions.technical_questions).map(([level, q_list]) => (
                          <div key={level} className="space-y-2">
                            <span className="text-[10px] font-extrabold tracking-wider uppercase bg-brand-50 dark:bg-brand-950/40 text-brand-700 dark:text-brand-300 px-2 py-0.5 rounded">
                              {level}
                            </span>
                            {q_list.map((q: any, i: number) => (
                              <div key={i} className="p-3 bg-slate-50 dark:bg-slate-950/20 border border-slate-200/50 dark:border-slate-800/40 rounded-xl text-xs">
                                <p className="font-semibold text-slate-800 dark:text-white">Q: {q.question}</p>
                                <p className="text-slate-500 dark:text-slate-400 mt-1.5 pl-2 border-l border-slate-300 dark:border-slate-700">
                                  <strong>Expected Answer:</strong> {q.answer}
                                </p>
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
