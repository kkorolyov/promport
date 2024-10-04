set -e

# mount scratch image
container=$(buildah from scratch)

# install packages to image
containermnt=$(buildah mount $container)
dnf install\
	--setopt cachedir=/var/cache/dnf\
	--setopt reposdir=/etc/yum.repos.d\
	--setopt install_weak_deps=false\
	--setopt tsflags=nodocs\
	--releasever 40\
	--installroot $containermnt\
	-y glibc-minimal-langpack python-pip
buildah unmount $container

# download and copy promtool to image
wget -O- "$PROMETHEUS_URL" | tar -xzf - --wildcards '*promtool' --strip-components=1
buildah copy $container promtool
rm -rf promtool

# install python module
buildah copy $container src/ src/
buildah copy $container pyproject.toml
python3 -m pip install --user .
buildah run $container rm -rf src pyproject.toml

# setup entrypoint
buildah config --entrypoint "python3 -m promport"

# publish
image=buildah commit $container promport
buildah rm $container
buildah push $image "docker://${REGISTRY}/promport:${TAG}"
