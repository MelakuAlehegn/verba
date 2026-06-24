import { Sparkles } from "lucide-react";

/** Verba's brand mark — a glossy emerald sphere orbited by dashed ellipses with
 *  floating source chips. Uses the Lovable "verba" palette. Decorative; motion
 *  is gated to motion-safe. */
export function BrandOrb() {
  return (
    <div className="relative mx-auto flex h-44 w-full max-w-lg items-center justify-center" aria-hidden>
      {/* Ambient glow — a centered circle big enough to contain the orbit at any
          rotation (the ellipse's long axis swings vertical as it spins). */}
      <div
        className="absolute left-1/2 top-1/2 h-[28rem] w-[28rem] max-w-[130vw] -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{
          background: "radial-gradient(circle, oklch(0.78 0.12 162 / 0.24), transparent 78%)",
        }}
      />

      {/* Orbiting dashed ellipses */}
      <svg
        viewBox="0 0 520 240"
        className="absolute h-44 w-[34rem] max-w-full motion-safe:animate-[spin_32s_linear_infinite]"
        style={{ color: "oklch(0.52 0.09 165)" }}
        fill="none"
      >
        <ellipse
          cx="260"
          cy="120"
          rx="214"
          ry="104"
          stroke="currentColor"
          strokeOpacity="0.3"
          strokeWidth="1.5"
          strokeDasharray="1 9"
          strokeLinecap="round"
        />
        <ellipse
          cx="260"
          cy="120"
          rx="152"
          ry="72"
          stroke="currentColor"
          strokeOpacity="0.22"
          strokeWidth="1.5"
          strokeDasharray="1 9"
          strokeLinecap="round"
        />
      </svg>

      {/* Sphere */}
      <div
        className="relative h-24 w-24 rounded-full motion-safe:animate-orb-float"
        style={{
          background:
            "radial-gradient(circle at 35% 28%, oklch(0.92 0.09 162) 0%, oklch(0.66 0.11 163) 30%, oklch(0.52 0.09 165) 58%, oklch(0.30 0.07 165) 100%)",
          boxShadow:
            "0 14px 50px oklch(0.52 0.09 165 / 0.45), inset 0 2px 6px oklch(0.92 0.10 162 / 0.5)",
        }}
      >
        <span className="absolute left-[26%] top-[22%] h-2.5 w-2.5 rounded-full bg-white/90 blur-[1px]" />
      </div>

      {/* Floating source chips */}
      <div className="absolute left-1/2 top-1/2 flex translate-x-3 translate-y-4 items-center">
        <span
          className="z-10 flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-semibold shadow-md ring-1 ring-black/5"
          style={{ color: "oklch(0.42 0.09 165)" }}
        >
          <Sparkles className="h-3 w-3" /> note
        </span>
        <span className="-ml-2 rounded-full bg-white px-2.5 py-1 text-xs font-medium text-zinc-500 shadow-md ring-1 ring-black/5">
          pdf
        </span>
      </div>
    </div>
  );
}
