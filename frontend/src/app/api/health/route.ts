/**
 * WHY THIS WAS CHOSEN:
 * This API endpoint provides a lightweight health check for the Next.js frontend application.
 * It is used by monitoring tools, load balancers, and container orchestration platforms 
 * to verify the application is running and responding to requests.
 */

import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ status: "healthy" });
}
