import React from 'react';
import { MigrationPlan } from '../../types';
import { Clock, Calendar, CheckCircle2, ArrowRight } from 'lucide-react';

interface TaskTimelineProps {
  plan: MigrationPlan;
}

export const TaskTimeline: React.FC<TaskTimelineProps> = ({ plan }) => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-6">
      {/* Overview Cards */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold font-mono text-slate-100">{plan.name}</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Plan ID: <span className="font-mono text-cyan-300">{plan.id.slice(0, 8)}</span> • Generated {new Date(plan.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 rounded-xl bg-slate-900 border border-slate-800 px-3.5 py-2 font-mono">
            <Clock className="w-4 h-4 text-cyan-400" />
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Effort</div>
              <div className="text-sm font-bold text-slate-200">{plan.total_person_days} Person-Days</div>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-xl bg-slate-900 border border-slate-800 px-3.5 py-2 font-mono">
            <Calendar className="w-4 h-4 text-purple-400" />
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Duration</div>
              <div className="text-sm font-bold text-purple-300">{plan.total_calendar_months} Months</div>
            </div>
          </div>
        </div>
      </div>

      {/* Task Roadmap List */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
          Sequenced Migration Tasks ({plan.tasks.length})
        </h4>

        {plan.tasks.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500">
            No specific tasks generated for this migration plan yet.
          </div>
        ) : (
          <div className="space-y-2.5">
            {plan.tasks.map((task, idx) => (
              <div
                key={task.id}
                className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-slate-900/70 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-950/70 border border-cyan-800/50 text-cyan-400 font-mono text-xs font-bold shrink-0">
                    {task.sequence_order || idx + 1}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200 font-mono">{task.title}</div>
                    {task.description && (
                      <div className="text-[11px] text-slate-400 mt-0.5">{task.description}</div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4 shrink-0 font-mono text-xs">
                  <div className="text-right">
                    <span className="text-slate-300 font-semibold">{task.person_days}d</span>
                    <span className="text-[10px] text-slate-500 block">estimated</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded border border-cyan-800/60 bg-cyan-950/60 text-cyan-400 font-semibold uppercase">
                    {task.status || 'PLANNED'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
