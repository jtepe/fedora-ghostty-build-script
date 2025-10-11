# Containerfile for building Ghostty terminal application
# This builds Ghostty in a container to avoid installing build dependencies locally

FROM fedora:latest

# Install build dependencies for Fedora
# Dependencies from: https://ghostty.org/docs/install/build#fedora
RUN dnf install -y \
    git \
    gtk4-devel \
    libadwaita-devel \
    gtk4-layer-shell-devel \
    gettext \
    gcc \
    gcc-c++ \
    oniguruma-devel \
    minisign \
    && dnf clean all

# Install curl and unzip for downloading Zig
RUN dnf install -y curl unzip && dnf clean all

# Download and extract Zig compiler
ARG ZIG_VERSION=0.14.1
WORKDIR /opt
RUN curl -sL https://ziglang.org/download/${ZIG_VERSION}/zig-x86_64-linux-${ZIG_VERSION}.tar.xz -o zig.tar.xz \
    && tar -xf zig.tar.xz \
    && mv zig-x86_64-linux-${ZIG_VERSION} zig \
    && rm zig.tar.xz

# Add Zig to PATH
ENV PATH="/opt/zig:${PATH}"

# Create a non-root user with UID 1000
RUN useradd -u 1000 -m builder

# Create build directory and set ownership
WORKDIR /build
RUN chown -R builder:builder /build

# Switch to non-root user
USER builder

# Download and extract Ghostty source
ENV GHOSTTY_PUB_KEY=RWQlAjJC23149WL2sEpT/l0QKy7hMIFhYdQOFy0Z7z7PbneUgvlsnYcV
ARG GHOSTTY_VERSION=1.2.0
RUN curl -sL https://release.files.ghostty.org/${GHOSTTY_VERSION}/ghostty-${GHOSTTY_VERSION}.tar.gz -O \
    && curl -sL https://release.files.ghostty.org/${GHOSTTY_VERSION}/ghostty-${GHOSTTY_VERSION}.tar.gz.minisig -O \
    && minisign -Vm ghostty-${GHOSTTY_VERSION}.tar.gz -P ${GHOSTTY_PUB_KEY} \
    && mv ghostty-${GHOSTTY_VERSION}.tar.gz ghostty.tar.gz \
    && tar -xzf ghostty.tar.gz \
    && rm ghostty.tar.gz

# Build Ghostty
WORKDIR /build/ghostty-${GHOSTTY_VERSION}
RUN zig build -p /build/output -Doptimize=ReleaseFast

# The built binary will be in /build/output/bin/ghostty
# To extract it, run:
# podman create --name ghostty-extract ghostty-builder
# podman cp ghostty-extract:/build/output/bin/ghostty ./ghostty
# podman rm ghostty-extract
