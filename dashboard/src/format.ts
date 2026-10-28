import type { DecisionKind, Status } from "./api";

const dollars = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});
const day = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
  timeZone: "UTC",
});
const clock = new Intl.DateTimeFormat("en-US", {
  hour: "numeric",
  minute: "2-digit",
  second: "2-digit",
});
const stamp = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export const STATUSES: Status[] = [
  "waiting",
  "in_progress",
  "waiting_for_sign_off",
  "decided",
];

export const STATUS_LABELS: Record<Status, string> = {
  waiting: "Waiting",
  in_progress: "In progress",
  waiting_for_sign_off: "Waiting for sign-off",
  decided: "Decided",
};

export const DECISION_LABELS: Record<DecisionKind, string> = {
  approve: "Approve",
  decline: "Decline",
  refer: "Refer",
};

export function money(amount: number): string {
  return dollars.format(amount);
}

/** A calendar date such as 2026-06-24, shown as Jun 24, 2026 */
export function date(iso: string): string {
  return day.format(new Date(iso));
}

/** The time of a timestamp, such as 9:52:54 AM */
export function time(iso: string): string {
  return clock.format(new Date(iso));
}

/** A timestamp, such as Oct 28, 2026, 9:52 AM */
export function moment(iso: string): string {
  return stamp.format(new Date(iso));
}

/** A code such as trip_delay, shown as Trip delay */
export function label(code: string): string {
  return code.charAt(0).toUpperCase() + code.slice(1).replaceAll("_", " ");
}

export function timeLeft(seconds: number): string {
  if (seconds === 0) return "Finishing up";
  if (seconds < 60) {
    return `About ${String(seconds)} second${seconds === 1 ? "" : "s"} left`;
  }
  const minutes = Math.round(seconds / 60);
  return `About ${String(minutes)} minute${minutes === 1 ? "" : "s"} left`;
}
