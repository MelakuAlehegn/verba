import { useCallback, useEffect, useState } from "react";
import useEmblaCarousel from "embla-carousel-react";
import { cn } from "@/lib/utils";

const SLIDES = [
  {
    title: "Answers grounded in your documents",
    description: "Upload your files once, then ask questions in plain language.",
  },
  {
    title: "Citations you can verify",
    description: "Every response links back to the source material that shaped it.",
  },
  {
    title: "Your knowledge, kept private",
    description: "Documents stay in your workspace — not a shared model training set.",
  },
] as const;

export function AuthBrandingPanel({ className }: { className?: string }) {
  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true });
  const [activeIndex, setActiveIndex] = useState(0);

  const onSelect = useCallback(() => {
    if (!emblaApi) return;
    setActiveIndex(emblaApi.selectedScrollSnap());
  }, [emblaApi]);

  useEffect(() => {
    if (!emblaApi) return;
    onSelect();
    emblaApi.on("select", onSelect);
    return () => {
      emblaApi.off("select", onSelect);
    };
  }, [emblaApi, onSelect]);

  useEffect(() => {
    if (!emblaApi) return;
    const timer = window.setInterval(() => {
      emblaApi.scrollNext();
    }, 6000);
    return () => window.clearInterval(timer);
  }, [emblaApi]);

  return (
    <div
      className={cn(
        "relative flex flex-col justify-between overflow-hidden bg-primary p-10 text-primary-foreground",
        className,
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-30"
        aria-hidden
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255,255,255,0.08) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255,255,255,0.08) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />
      <div
        className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -bottom-16 -left-16 h-64 w-64 rounded-full bg-black/10 blur-3xl"
        aria-hidden
      />

      <div className="relative z-10">
        <span className="text-xl font-semibold tracking-tight">Verba</span>
      </div>

      <div className="relative z-10 flex flex-1 flex-col justify-center py-12">
        <div ref={emblaRef} className="overflow-hidden">
          <div className="flex">
            {SLIDES.map((slide) => (
              <div key={slide.title} className="min-w-0 shrink-0 grow-0 basis-full pr-4">
                <h2 className="text-3xl font-semibold leading-tight tracking-tight">
                  {slide.title}
                </h2>
                <p className="mt-4 max-w-md text-base leading-relaxed text-primary-foreground/80">
                  {slide.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-10 flex gap-2">
          {SLIDES.map((slide, index) => (
            <button
              key={slide.title}
              type="button"
              aria-label={`Show slide ${index + 1}`}
              onClick={() => emblaApi?.scrollTo(index)}
              className={cn(
                "h-1.5 rounded-full transition-all duration-300",
                index === activeIndex ? "w-8 bg-primary-foreground" : "w-1.5 bg-primary-foreground/40",
              )}
            />
          ))}
        </div>
      </div>

      <p className="relative z-10 text-sm text-primary-foreground/60">
        Document Q&amp;A for teams who need sources, not guesses.
      </p>
    </div>
  );
}
