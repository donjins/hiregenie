import React, { useState, useEffect } from 'react';
import { schedulerService, candidateService } from '../services/api';
import { Interview, Candidate } from '../types';
import { Calendar, Video, Loader, User, Clock, Check, XCircle } from 'lucide-react';

export const Scheduler: React.FC = () => {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [slots, setSlots] = useState<string[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);

  // Form Booking state
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [selectedSlot, setSelectedSlot] = useState('');
  
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ints, avSlots, cands] = await Promise.all([
          schedulerService.listInterviews(),
          schedulerService.listSlots(),
          candidateService.list()
        ]);
        setInterviews(ints);
        setSlots(avSlots);
        // Candidate selection should only include candidates without scheduled interviews
        setCandidates(cands.filter(c => !c.interview_scheduled));
      } catch (err) {
        setError('Failed to fetch schedule data.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [success]);

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess('');
    setError('');

    if (!selectedCandidateId || !selectedSlot) {
      setError('Please select both a candidate and an available slot.');
      return;
    }

    const candObj = candidates.find(c => c.id === selectedCandidateId);
    if (!candObj) return;

    try {
      await schedulerService.schedule({
        candidate_id: selectedCandidateId,
        candidate_name: candObj.name,
        job_title: "Software Developer", // Default job context or fetch details
        time_slot: selectedSlot
      });
      setSuccess(`Interview booked for ${candObj.name} at ${selectedSlot}!`);
      setSelectedCandidateId('');
      setSelectedSlot('');
    } catch (err) {
      setError('Failed to book the interview slot.');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-outfit font-bold text-3xl text-slate-900 dark:text-white">Interview Scheduler</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Orchestrate interviewer calendars, check availability, and send invites.</p>
      </div>

      {success && (
        <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 text-emerald-600 dark:text-emerald-400 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>{success}</span>
        </div>
      )}
      {error && (
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
          <XCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Booking Form */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm space-y-6">
          <h3 className="font-outfit font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-brand-600" />
            <span>Book Interview Slot</span>
          </h3>

          <form onSubmit={handleBook} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Select Candidate
              </label>
              <select
                value={selectedCandidateId}
                onChange={(e) => setSelectedCandidateId(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
              >
                <option value="">-- Choose Candidate --</option>
                {candidates.map((c) => (
                  <option key={c.id} value={c.id}>{c.name} ({c.email})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Select Available Time Slot
              </label>
              <select
                value={selectedSlot}
                onChange={(e) => setSelectedSlot(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
              >
                <option value="">-- Select Time Slot --</option>
                {slots.map((s, idx) => (
                  <option key={idx} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white rounded-xl text-sm font-semibold active:scale-95 transition-all shadow-md"
            >
              Confirm Interview Schedule
            </button>
          </form>
        </div>

        {/* Booked list */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-outfit font-bold text-lg text-slate-800 dark:text-white">Active Recruiter Calendar</h3>

          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader className="w-8 h-8 animate-spin text-brand-600" />
              </div>
            ) : (
              interviews.map((int) => (
                <div key={int.id} className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-brand-50 dark:bg-brand-950/20 text-brand-600 dark:text-brand-400 flex items-center justify-center shrink-0">
                      <Clock className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="font-outfit font-bold text-base text-slate-800 dark:text-white flex items-center gap-2">
                        <span>{int.candidate_name}</span>
                        <span className="text-[10px] uppercase font-extrabold tracking-wider bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded">
                          {int.status}
                        </span>
                      </h4>
                      <div className="text-xs text-slate-400 mt-1 space-y-1">
                        <p className="flex items-center gap-1">
                          <User className="w-3.5 h-3.5" /> 
                          <span>Interviewer: {int.interviewer} ({int.interviewer_email})</span>
                        </p>
                        <p className="flex items-center gap-1 font-semibold text-brand-600 dark:text-brand-400">
                          <Clock className="w-3.5 h-3.5" /> 
                          <span>Time: {int.time_slot}</span>
                        </p>
                      </div>
                    </div>
                  </div>

                  <a
                    href={int.meeting_link}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-center gap-2 px-4 py-2 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700/80 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 transition-colors"
                  >
                    <Video className="w-4 h-4 text-brand-500" />
                    <span>Join Google Meet</span>
                  </a>
                </div>
              ))
            )}

            {!loading && !interviews.length && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/40 p-12 rounded-2xl text-center text-slate-400 text-sm">
                No interviews scheduled yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
