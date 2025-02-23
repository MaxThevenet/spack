# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""Caches used by Spack to store data"""
import os
from typing import Union

import llnl.util.lang
from llnl.util.filesystem import mkdirp
from llnl.util.symlink import symlink

import spack.config
import spack.error
import spack.fetch_strategy
import spack.paths
import spack.util.file_cache
import spack.util.path


def misc_cache_location():
    """The ``misc_cache`` is Spack's cache for small data.

    Currently the ``misc_cache`` stores indexes for virtual dependency
    providers and for which packages provide which tags.
    """
    path = spack.config.get("config:misc_cache", spack.paths.default_misc_cache_path)
    return spack.util.path.canonicalize_path(path)


def _misc_cache():
    path = misc_cache_location()
    return spack.util.file_cache.FileCache(path)


#: Spack's cache for small data
misc_cache: Union[
    spack.util.file_cache.FileCache, llnl.util.lang.Singleton
] = llnl.util.lang.Singleton(_misc_cache)


def fetch_cache_location():
    """Filesystem cache of downloaded archives.

    This prevents Spack from repeatedly fetch the same files when
    building the same package different ways or multiple times.
    """
    path = spack.config.get("config:source_cache")
    if not path:
        path = spack.paths.default_fetch_cache_path
    path = spack.util.path.canonicalize_path(path)
    return path


def _fetch_cache():
    path = fetch_cache_location()
    return spack.fetch_strategy.FsCache(path)


class MirrorCache:
    def __init__(self, root, skip_unstable_versions):
        self.root = os.path.abspath(root)
        self.skip_unstable_versions = skip_unstable_versions

    def store(self, fetcher, relative_dest):
        """Fetch and relocate the fetcher's target into our mirror cache."""

        # Note this will archive package sources even if they would not
        # normally be cached (e.g. the current tip of an hg/git branch)
        dst = os.path.join(self.root, relative_dest)
        mkdirp(os.path.dirname(dst))
        fetcher.archive(dst)

    def symlink(self, mirror_ref):
        """Symlink a human readible path in our mirror to the actual
        storage location."""

        cosmetic_path = os.path.join(self.root, mirror_ref.cosmetic_path)
        storage_path = os.path.join(self.root, mirror_ref.storage_path)
        relative_dst = os.path.relpath(storage_path, start=os.path.dirname(cosmetic_path))

        if not os.path.exists(cosmetic_path):
            if os.path.lexists(cosmetic_path):
                # In this case the link itself exists but it is broken: remove
                # it and recreate it (in order to fix any symlinks broken prior
                # to https://github.com/spack/spack/pull/13908)
                os.unlink(cosmetic_path)
            mkdirp(os.path.dirname(cosmetic_path))
            symlink(relative_dst, cosmetic_path)


#: Spack's local cache for downloaded source archives
fetch_cache: Union[
    spack.fetch_strategy.FsCache, llnl.util.lang.Singleton
] = llnl.util.lang.Singleton(_fetch_cache)
