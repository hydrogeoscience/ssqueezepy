# -*- coding: utf-8 -*-
"""Test computation of various wavelet properties (time-frequency resolution,
center frequency, etc).
"""
import pytest
import numpy as np
import matplotlib.pyplot as plt
from ssqueezepy.wavelets import Wavelet, time_resolution, freq_resolution
from ssqueezepy.wavelets import center_frequency
from ssqueezepy.viz_toolkit import scat

VIZ = 0  # set to 1 to enable various visuals


def test_energy_center_frequency():
    # if kind='energy' passes, long shot for 'peak' to fail, so just test former
    def _test_mu_dependence(wc0, mu0, scale0, N0, th):
        """wc ~ mu"""
        mus = np.arange(mu0 + 1, 21)
        errs = np.zeros(len(mus))

        for i, mu in enumerate(mus):
            psihfn = Wavelet(('morlet', {'mu': mu}))
            wc = center_frequency(psihfn, scale=scale0, kind='energy')
            errs[i] = abs((wc / wc0) - (mu / mu0))

        _assert_and_viz(th, errs, mus, 'mu',
                        "Center frequency (energy), morlet")

    def _test_scale_dependence(wc0, mu0, scale0, N0, th):
        """wc ~ 1/scale

        For small `scale`, the bell is trimmed and the (energy) center frequency
        is no longer at mode/peak (both of which are also trimmed), but is
        less; we don't test these to keep code clean.
        """
        scales = 2**(np.arange(16, 81) / 8)  # [4, ..., 1024]
        errs = np.zeros(len(scales))
        psihfn = Wavelet(('morlet', {'mu': mu0}))

        for i, scale in enumerate(scales):
            wc = center_frequency(psihfn, scale=scale, kind='energy')
            errs[i] = abs((wc / wc0) - (scale0 / scale))

        _assert_and_viz(th, errs, np.log2(scales), 'log2(scale)',
                        "Center frequency (energy), morlet")

    def _test_N_dependence(wc0, mu0, scale0, N0, th):
        """Independent"""
        Ns = (np.array([.25, .5, 2, 4, 9]) * N0).astype('int64')
        errs = np.zeros(len(Ns))
        psihfn = Wavelet(('morlet', {'mu': mu0}))

        for i, N in enumerate(Ns):
            wc = center_frequency(psihfn, scale=scale0, N=N, kind='energy')
            errs[i] = abs(wc - wc0)

        _assert_and_viz(th, errs, Ns, 'N',
                        "Center frequency (energy), morlet")

    mu0 = 5
    scale0 = 10
    N0 = 1024

    psihfn0 = Wavelet(('morlet', {'mu': mu0}))
    wc0 = center_frequency(psihfn0, scale=scale0, N=N0, kind='energy')

    args = (wc0, mu0, scale0, N0)
    _test_mu_dependence(   *args, th=1e-7)
    _test_scale_dependence(*args, th=1e-9)
    _test_N_dependence(    *args, th=1e-14)


def test_time_resolution():
    def _test_mu_dependence(std_t_nd0, std_t_d0, mu0, scale0, N0, th):
        """Nondimensional: std_t ~ 1/mu -- Dimensional: independent"""
        mus = np.arange(mu0 + 1, 21)
        errs = np.zeros(2 * len(mus))

        for i, mu in enumerate(mus):
            psihfn = Wavelet(('morlet', {'mu': mu}))
            std_t_nd = time_resolution(psihfn, scale0, N0, nondim=True)
            std_t_d  = time_resolution(psihfn, scale0, N0, nondim=False)

            errs[2*i]     = abs((std_t_nd / std_t_nd0) - (mu / mu0))
            errs[2*i + 1] = abs(std_t_d - std_t_d0)

        _assert_and_viz(th, errs, np.repeat(mus, 2), 'mu',
                        "Time resolution, morlet")

    def _test_scale_dependence(std_t_nd0, std_t_d0, mu0, scale0, N0, th):
        """Nondimensional: independent* -- Dimensional: std_t ~ scale.

        *Nondimensional breaks down for low scales (<~3), where freq-domain
        wavelet is trimmed (even beyond mode), deviating center frequency from
        continuous-time counterpart.

        Particularly large `th` per `min_decay` default of 1e6 in
        `time_resolution`, which reasonably limits the extended wavelet
        duration in time-domain in (paddded) CWT (but this limitation might be
        undue; I'm unsure. https://dsp.stackexchange.com/q/70810/50076).
        """
        scales = 2**(np.arange(16, 81) / 8)  # [4, ..., 1024]
        errs = np.zeros(2 * len(scales))
        psihfn = Wavelet(('morlet', {'mu': mu0}))

        for i, scale in enumerate(scales):
            std_t_nd = time_resolution(psihfn, scale, N0, nondim=True)
            std_t_d  = time_resolution(psihfn, scale, N0, nondim=False)

            errs[2*i]     = abs(std_t_nd  - std_t_nd0)
            errs[2*i + 1] = abs((std_t_d / std_t_d0) - (scale / scale0))

        _assert_and_viz(th, errs, np.repeat(np.log2(scales), 2), 'log2(scale)',
                        "Time resolution, morlet")

    def _test_N_dependence(std_t_nd0, std_t_d0, mu0, scale0, N0, th):
        """Independent

        `th` can be 1e-14 if dropping odd-sampled case where time-domain wavelet
        has suboptimal decay: https://github.com/jonathanlilly/jLab/issues/13
        (also dropping low-sampled case)
        """
        Ns = (np.array([.1, 1/3, .5, 2, 4, 9]) * N0).astype('int64')
        errs = np.zeros(2 * len(Ns))
        psihfn = Wavelet(('morlet', {'mu': mu0}))

        for i, N in enumerate(Ns):
            std_t_nd = time_resolution(psihfn, scale0, N, nondim=True)
            std_t_d  = time_resolution(psihfn, scale0, N, nondim=False)

            errs[2*i]     = abs(std_t_nd - std_t_nd0)
            errs[2*i + 1] = abs(std_t_d  - std_t_d0)

        _assert_and_viz(th, errs, np.repeat(Ns, 2), 'N',
                        "Time resolution, morlet")

    mu0 = 5
    scale0 = 10
    N0 = 1024

    psihfn0 = Wavelet(('morlet', {'mu': mu0}))
    std_t_nd0 = time_resolution(psihfn0, scale0, N0, nondim=True)
    std_t_d0  = time_resolution(psihfn0, scale0, N0, nondim=False)

    args = (std_t_nd0, std_t_d0, mu0, scale0, N0)
    _test_mu_dependence(   *args, th=1e-6)
    _test_scale_dependence(*args, th=2e-3)
    _test_N_dependence(    *args, th=1e-9)


def test_freq_resolution():
    def _test_mu_dependence(std_w_nd0, std_w_d0, mu0, scale0, N0, th):
        """Nondimensional: std_w ~ mu -- Dimensional: independent"""
        mus = np.arange(mu0 + 1, 21)
        errs = np.zeros(2 * len(mus))

        for i, mu in enumerate(mus):
            psihfn = Wavelet(('morlet', {'mu': mu}))
            std_w_nd = freq_resolution(psihfn, scale0, N0, nondim=True)
            std_w_d  = freq_resolution(psihfn, scale0, N0, nondim=False)

            errs[2*i]     = abs((std_w_nd / std_w_nd0) - (mu0 / mu))
            errs[2*i + 1] = abs(std_w_d - std_w_d0)

        _assert_and_viz(th, errs, np.repeat(mus, 2), 'mu',
                        "Frequency resolution, morlet")

    def _test_scale_dependence(std_w_nd0, std_w_d0, mu0, scale0, N0, th):
        """Nondimensional: independent* -- Dimensional: std_w ~ 1/scale

        Particularly large `th` per nontrivial discretization finite-precision
        error for large scales, with small number of samples representing
        the non-zero region. We don't "fix" this to match continuous-time
        behavior again since it's more accurate per our CWT.
        """
        scales = 2**(np.arange(16, 81) / 8)  # [4, ..., 1024]
        errs = np.zeros(2 * len(scales))
        psihfn = Wavelet(('morlet', {'mu': mu0}))

        for i, scale in enumerate(scales):
            std_w_nd = freq_resolution(psihfn, scale, N0, nondim=True)
            std_w_d  = freq_resolution(psihfn, scale, N0, nondim=False)

            errs[2*i]     = abs(std_w_nd  - std_w_nd0)
            errs[2*i + 1] = abs((std_w_d / std_w_d0) - (scale0 / scale))

        _assert_and_viz(th, errs, np.repeat(np.log2(scales), 2), 'log2(scale)',
                        "Frequency resolution, morlet")

    def _test_N_dependence(std_w_nd0, std_w_d0, mu0, scale0, N0, th):
        """Independent"""
        Ns = (np.array([.25, .5, 2, 4, 9]) * N0).astype('int64')
        errs = np.zeros(2 * len(Ns))
        psihfn = Wavelet(('morlet', {'mu': mu0}))

        for i, N in enumerate(Ns):
            std_w_nd = freq_resolution(psihfn, scale0, N, nondim=True)
            std_w_d  = freq_resolution(psihfn, scale0, N, nondim=False)

            errs[2*i]     = abs(std_w_nd - std_w_nd0)
            errs[2*i + 1] = abs(std_w_d  - std_w_d0)

        _assert_and_viz(th, errs, np.repeat(Ns, 2), 'N',
                        "Frequency resolution, morlet")

    mu0 = 5
    scale0 = 10
    N0 = 1024

    psihfn0 = Wavelet(('morlet', {'mu': mu0}))
    std_w_nd0 = freq_resolution(psihfn0, scale0, N0, nondim=True)
    std_w_d0  = freq_resolution(psihfn0, scale0, N0, nondim=False)

    args = (std_w_nd0, std_w_d0, mu0, scale0, N0)
    _test_mu_dependence(   *args, th=1e-6)
    _test_scale_dependence(*args, th=3e-1)
    _test_N_dependence(    *args, th=1e-11)


def _assert_and_viz(th, errs, params, pname, test_name, logscale=True):
    had_error = False
    for err, param in zip(errs, params):
        if err > th:
            had_error = True
            break

    if VIZ:
        title=f"{test_name}: abs(err) vs {pname}"
        if logscale:
            title = title.replace("abs(err)", "log10(abs(err))")
            errs[errs < 1e-15] = 1e-15
            errs = np.log10(errs)
            th = np.log10(th)
        scat(params, errs, title=title)
        plt.axhline(th, color='tab:red')
        plt.show()

    if had_error:
        raise AssertionError("%.2e > %.1e, %s=%.2f" % (err, th, pname, param))


if __name__ == '__main__':
    pytest.main([__file__, "-s"])