import React, { useState, useEffect } from 'react';
import { emailService } from '../services/api';
import { EmailRecord } from '../types';
import { Mail, Check, AlertCircle, Loader } from 'lucide-react';

export const Emails: React.FC = () => {
  const [emails, setEmails] = useState<EmailRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Selected Email Drawer for content review
  const [selectedEmail, setSelectedEmail] = useState<EmailRecord | null>(null);

  useEffect(() => {
    const fetchEmails = async () => {
      try {
        const data = await emailService.listHistory();
        setEmails(data);
      } catch (err) {
        setError('Failed to load email history.');
      } finally {
        setLoading(false);
      }
    };
    fetchEmails();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-outfit font-bold text-3xl text-slate-900 dark:text-white">Email Communications Log</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Audit log of auto-generated candidate alerts and scheduling notifications.</p>
        {error && <div className="text-rose-500 mt-2 text-sm">{error}</div>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Email History Table */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm lg:col-span-2">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <th className="pb-3 pl-2">Recipient</th>
                  <th className="pb-3">Subject / Type</th>
                  <th className="pb-3">Sent Time</th>
                  <th className="pb-3 pr-2 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="py-10 text-center">
                      <Loader className="w-6 h-6 animate-spin text-brand-600 mx-auto" />
                    </td>
                  </tr>
                ) : (
                  emails.map((mail) => {
                    const recipient = mail.recipient_email || (mail as any).to || 'Unknown';
                    const name = mail.candidate_name || recipient.split('@')[0] || 'Candidate';
                    const emailType = mail.type || 'invitation';
                    const status = mail.status || 'Sent';
                    
                    let sentTime = 'N/A';
                    if (mail.sent_at) {
                      const d = new Date(mail.sent_at);
                      if (!isNaN(d.getTime())) {
                        sentTime = d.toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
                      }
                    }

                    return (
                      <tr 
                        key={mail.id}
                        onClick={() => setSelectedEmail(mail)}
                        className={`hover:bg-slate-50/50 dark:hover:bg-slate-800/20 cursor-pointer ${
                          selectedEmail?.id === mail.id ? 'bg-slate-50 dark:bg-slate-800/40' : ''
                        }`}
                      >
                        <td className="py-4 pl-2 font-semibold text-slate-800 dark:text-white">
                          {name}
                          <span className="text-[10px] text-slate-400 block font-normal mt-0.5">{recipient}</span>
                        </td>
                        <td className="py-4">
                          <span className="font-medium text-slate-700 dark:text-slate-350">{mail.subject}</span>
                          <div className="mt-1">
                            <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                              emailType === 'invitation'
                                ? 'bg-blue-50 text-blue-600 dark:bg-blue-950/20 dark:text-brand-400'
                                : emailType === 'shortlist'
                                ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/20 dark:text-amber-400'
                                : emailType === 'rejection'
                                ? 'bg-rose-50 text-rose-600 dark:bg-rose-950/20 dark:text-rose-400'
                                : 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-400'
                            }`}>
                              {emailType}
                            </span>
                          </div>
                        </td>
                        <td className="py-4 text-slate-400">
                          {sentTime}
                        </td>
                        <td className="py-4 pr-2 text-right">
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 px-2 py-0.5 rounded-full">
                            <Check className="w-3 h-3" />
                            <span>{status}</span>
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}

                {!loading && !emails.length && (
                  <tr>
                    <td colSpan={4} className="py-12 text-center text-slate-400">
                      No automated emails sent yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Live Email Preview Pane */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm flex flex-col min-h-[300px]">
          <h3 className="font-outfit font-bold text-base text-slate-800 dark:text-white border-b border-slate-100 dark:border-slate-800/60 pb-3 flex items-center gap-2">
            <Mail className="w-5 h-5 text-brand-600" />
            <span>Email Preview Canvas</span>
          </h3>

          {selectedEmail ? (
            <div className="mt-4 flex-1 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="text-xs bg-slate-50 dark:bg-slate-950/40 p-3 rounded-xl space-y-1.5">
                  <p className="text-slate-400"><strong>To:</strong> {selectedEmail.candidate_name} &lt;{selectedEmail.recipient_email}&gt;</p>
                  <p className="text-slate-450"><strong>Subject:</strong> {selectedEmail.subject}</p>
                </div>
                
                <div className="text-xs text-slate-650 dark:text-slate-300 leading-relaxed font-mono whitespace-pre-wrap bg-slate-50/50 dark:bg-slate-950/20 p-4 rounded-xl border border-slate-100 dark:border-slate-800/50 max-h-[350px] overflow-y-auto">
                  {selectedEmail.body}
                </div>
              </div>

              <div className="text-[10px] text-slate-400 mt-4 text-center">
                This email was dispatched via Mock SMTP dispatch logs.
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-slate-400 py-10">
              <AlertCircle className="w-8 h-8 text-slate-300 dark:text-slate-700 mb-2" />
              <p className="text-xs">Select an email record from the list to preview its generated contents.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
