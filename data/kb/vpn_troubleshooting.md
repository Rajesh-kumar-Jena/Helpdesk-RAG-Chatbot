# VPN Connection Troubleshooting

## "Connection failed" or timeout errors
1. Confirm you have a working internet connection (try loading any website).
2. Fully quit the VPN client (not just disconnect) and reopen it.
3. Switch the VPN server/region in the client settings — the nearest
   server may be overloaded.
4. Restart your computer if the client still won't connect after a
   server switch.

## VPN connects but you can't reach internal sites
1. Confirm the internal site URL is correct and only accessible on VPN.
2. Run `ipconfig /flushdns` (Windows) or `sudo dscacheutil -flushcache`
   (Mac) to clear stale DNS entries.
3. Disconnect and reconnect the VPN — this often reassigns a working
   internal DNS server.
4. Check whether split-tunneling is enabled; some internal tools require
   full-tunnel mode.

## VPN keeps disconnecting randomly
- This is commonly caused by unstable Wi-Fi or an aggressive power-saving
  setting on the network adapter. Try a wired connection to confirm.
- Corporate firewalls at hotels/cafes sometimes block VPN ports outright;
  try a mobile hotspot to isolate the issue.

## Known limitations
This assistant cannot issue new VPN certificates or grant access to
network segments you don't already have permission for — those requests
require a manual review by network engineering.
