import type { ClientIdentity } from "../types";


const DEVICE_ID_KEY = "ara-device-id";
let currentIdentity: ClientIdentity | null = null;


function browserName(userAgent: string): string {
  if (userAgent.includes("Edg/")) return "Edge";
  if (userAgent.includes("Chrome/")) return "Chrome";
  if (userAgent.includes("Firefox/")) return "Firefox";
  if (userAgent.includes("Safari/")) return "Safari";
  return "Browser";
}

function newDeviceId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return "device-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function getOrCreateDeviceIdentity(): ClientIdentity {
  let deviceId = localStorage.getItem(DEVICE_ID_KEY);
  if (!deviceId) {
    deviceId = newDeviceId();
    localStorage.setItem(DEVICE_ID_KEY, deviceId);
  }

  const enrichedNavigator = navigator as Navigator & {
    userAgentData?: { platform?: string };
  };
  const platform =
    enrichedNavigator.userAgentData?.platform || navigator.platform || "Device";
  const label = `${platform} - ${browserName(navigator.userAgent)} - ${deviceId.slice(-6)}`;
  return { deviceId, deviceLabel: label };
}

export function configureClientIdentity(identity: ClientIdentity): void {
  currentIdentity = identity;
}

export function setGoogleCredential(credential: string | null): void {
  if (!currentIdentity) return;
  currentIdentity = { ...currentIdentity, googleCredential: credential || undefined };
}

export function identityHeaders(): Record<string, string> {
  if (!currentIdentity) return {};
  const headers: Record<string, string> = {
    "X-Device-Id": currentIdentity.deviceId,
    "X-Device-Label": currentIdentity.deviceLabel,
  };
  if (currentIdentity.googleCredential) {
    headers.Authorization = `Bearer ${currentIdentity.googleCredential}`;
  }
  return headers;
}
