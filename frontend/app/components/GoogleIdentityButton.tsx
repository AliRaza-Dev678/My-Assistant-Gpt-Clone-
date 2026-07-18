"use client";

import Script from "next/script";
import { useEffect, useRef, useState } from "react";


interface GoogleCredentialResponse {
  credential?: string;
}

interface GoogleAccountsApi {
  id: {
    initialize(options: {
      client_id: string;
      callback: (response: GoogleCredentialResponse) => void;
    }): void;
    renderButton(
      element: HTMLElement,
      options: Record<string, string | number>,
    ): void;
    disableAutoSelect(): void;
  };
}

declare global {
  interface Window {
    google?: { accounts: GoogleAccountsApi };
  }
}

interface GoogleIdentityButtonProps {
  clientId: string;
  onCredential: (credential: string) => void;
}

export function GoogleIdentityButton({
  clientId,
  onCredential,
}: GoogleIdentityButtonProps) {
  const [ready, setReady] = useState(false);
  const buttonRef = useRef<HTMLDivElement | null>(null);
  const callbackRef = useRef(onCredential);

  useEffect(() => {
    callbackRef.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    if (!ready || !buttonRef.current || !window.google) return;
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        if (response.credential) callbackRef.current(response.credential);
      },
    });
    buttonRef.current.replaceChildren();
    window.google.accounts.id.renderButton(buttonRef.current, {
      type: "standard",
      theme: "outline",
      size: "medium",
      shape: "pill",
      text: "continue_with",
      width: 238,
    });
  }, [clientId, ready]);

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={() => setReady(true)}
      />
      <div className="google-sign-in" ref={buttonRef} />
    </>
  );
}
