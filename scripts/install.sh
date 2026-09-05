#!/usr/bin/env bash
# Agam Toolchain Installer (Linux / macOS)
# Usage: curl -sSf https://agam.org/install.sh | sh

set -euo pipefail

AGAM_HOME="${HOME}/.agam"
BIN_DIR="${AGAM_HOME}/bin"
RELEASE_URL="https://github.com/agam-lang/agam/releases/latest/download"

echo "============================================================"
echo "⚡ Installing Agam Language & Toolchain (S-Grade Native LLVM)"
echo "============================================================"

# Detect Architecture and OS
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "${ARCH}" in
    x86_64|amd64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="aarch64" ;;
    *) echo "❌ Unsupported architecture: ${ARCH}"; exit 1 ;;
esac

case "${OS}" in
    linux) TARGET="${ARCH}-unknown-linux-gnu" ;;
    darwin) TARGET="${ARCH}-apple-darwin" ;;
    *) echo "❌ Unsupported operating system: ${OS}"; exit 1 ;;
esac

echo "Detected Platform: ${TARGET}"

mkdir -p "${BIN_DIR}"

# Check if building from local repository or downloading release archive
if [ -f "agam/Cargo.toml" ]; then
    echo "📦 Building native release binary from source repository..."
    cargo build --release --manifest-path agam/Cargo.toml --bin agamc
    cp agam/target/release/agamc "${BIN_DIR}/agamc"
else
    echo "⬇️ Downloading pre-compiled SDK bundle for ${TARGET}..."
    ARCHIVE_NAME="agam-sdk-${TARGET}.tar.gz"
    TMP_DIR="$(mktemp -d)"
    curl -fsSL "${RELEASE_URL}/${ARCHIVE_NAME}" -o "${TMP_DIR}/${ARCHIVE_NAME}"
    tar -xzf "${TMP_DIR}/${ARCHIVE_NAME}" -C "${AGAM_HOME}"
    rm -rf "${TMP_DIR}"
fi

chmod +x "${BIN_DIR}/agamc"

# Configure PATH in Shell Profile
SHELL_PROFILE="${HOME}/.bashrc"
if [ -n "${ZSH_VERSION:-}" ] || [ -f "${HOME}/.zshrc" ]; then
    SHELL_PROFILE="${HOME}/.zshrc"
fi

if ! grep -q "AGAM_HOME" "${SHELL_PROFILE}" 2>/dev/null; then
    echo "" >> "${SHELL_PROFILE}"
    echo "# Agam Toolchain Environment" >> "${SHELL_PROFILE}"
    echo "export AGAM_HOME=\"${AGAM_HOME}\"" >> "${SHELL_PROFILE}"
    echo "export PATH=\"\${AGAM_HOME}/bin:\$PATH\"" >> "${SHELL_PROFILE}"
    echo "✅ Added ~/.agam/bin to ${SHELL_PROFILE}"
fi

echo "============================================================"
echo "🎉 Agam Toolchain installed successfully!"
echo "Run 'source ${SHELL_PROFILE}' or start a new terminal session."
echo "Verify installation with: agamc doctor"
echo "============================================================"
