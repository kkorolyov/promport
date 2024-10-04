set -e

cwd=$(dirname "$0")

# mount scratch
container=$(buildah from scratch)
containermnt=$(buildah mount $container)

# install packages
dnf install\
	--setopt cachedir=/var/cache/dnf\
	--setopt reposdir=/etc/yum.repos.d\
	--setopt install_weak_deps=false\
	--setopt tsflags=nodocs\
	--releasever 40\
	--installroot $containermnt\
	-y\
	glibc-minimal-langpack python-pip

# download and copy promtool
wget -O- "$PROMETHEUS_URL" | tar -C $cwd -xzf - --wildcards '*promtool' --strip-components=1
buildah copy $container ${cwd}/promtool

# install python module
pip3 install --prefix=${containermnt}/usr $cwd

# setup entrypoint
buildah config --entrypoint "python3 -m promport" $container

# publish
image=$(buildah commit $container)
buildah rm $container
buildah push --tls-verify=false $image "docker://${REGISTRY}/promport:${TAG}"
