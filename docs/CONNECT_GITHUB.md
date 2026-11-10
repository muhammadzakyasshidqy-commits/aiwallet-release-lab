# GitHub authorization for source publication

The account `muhammadzakyasshidqy-commits` is connected for reads, but tested writes to `aiwallet-studio-qz-2026` returned `403 Resource not accessible by integration`. The existing repo is a website and must not be replaced. A new repo `aiwallet-release-lab` should be created only after authorizing a GitHub App with **Contents: Read and write** permission for the chosen repository.

In GitHub, open **Settings → Applications → Installed GitHub Apps** (https://github.com/settings/installations). Select the app attached to ChatGPT, inspect permissions and repository access, and select the new repository if the app provides Contents-write. Reconnect it in ChatGPT **Settings → Plugins → GitHub** if needed. Do not paste access tokens, passwords or OTP into a chat. If the app is not granted Contents-write by its installation schema, simply logging in again will not fix the scope.

When the app can write, verify a canary source file, then import the prepared source via GitHub Git Data API in one tree/commit update (or a verified bundle push on a repository you own), enable Actions and publish the v0.8 release assets. Do not claim success before checking the canonical public URL.
