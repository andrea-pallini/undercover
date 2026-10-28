import { expect, it } from "vitest";
import { date, label, money, timeLeft } from "./format";

it("formats money in US dollars", () => {
  expect(money(1250)).toBe("$1,250.00");
});

it("formats calendar dates", () => {
  expect(date("2026-06-24")).toBe("Jun 24, 2026");
});

it("turns codes into labels", () => {
  expect(label("emergency_medical")).toBe("Emergency medical");
});

it("describes the time left", () => {
  expect(timeLeft(0)).toBe("Finishing up");
  expect(timeLeft(1)).toBe("About 1 second left");
  expect(timeLeft(20)).toBe("About 20 seconds left");
  expect(timeLeft(70)).toBe("About 1 minute left");
  expect(timeLeft(150)).toBe("About 3 minutes left");
});
