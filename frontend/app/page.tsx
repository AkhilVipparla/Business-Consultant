import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 text-center">
      <h1 className="font-heading text-4xl font-bold text-charcoal">VentureMind AI</h1>
      <p className="mt-4 max-w-xl text-lg text-muted">
        An AI-powered Venture Studio that validates, improves, and evaluates startup ideas using a
        team of specialized AI agents.
      </p>
      <Button asChild size="default" variant="primary" className="mt-8">
        <Link href="/ventures/new">Validate a new idea</Link>
      </Button>
    </main>
  );
}
