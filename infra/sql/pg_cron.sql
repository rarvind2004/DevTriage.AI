CREATE EXTENSION IF NOT EXISTS pg_cron;
-- index and helper view for upcoming timers
CREATE INDEX IF NOT EXISTS idx_slatimer_deadline ON "SLATimer"("deadline") WHERE fired = false;
