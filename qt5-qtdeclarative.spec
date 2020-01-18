
%global qt_module qtdeclarative

# define to build docs, need to undef this for bootstrapping
# where qt5-qttools builds are not yet available
# only primary archs (for now), allow secondary to bootstrap
# global bootstrap 1

%if ! 0%{?bootstrap}
%global docs 1
%global tests 0
%endif

%if 0
#ifarch %{ix86}
%global nosse2_hack 1
## TODO:
# * consider debian's approach of runtime detection instead:
#   https://codereview.qt-project.org/#/c/127354/
%endif

# definition borrowed from qtbase
%global multilib_archs x86_64 %{ix86} %{?mips} ppc64 ppc s390x s390 sparc64 sparcv9

Summary: Qt5 - QtDeclarative component
Name:    qt5-%{qt_module}
Version: 5.9.2
Release: 1%{?dist}

# See LICENSE.GPL LICENSE.LGPL LGPL_EXCEPTION.txt, for details
License: LGPLv2 with exceptions or GPLv3 with exceptions
Url:     http://www.qt.io
Source0: http://download.qt.io/official_releases/qt/5.9/%{version}/submodules/%{qt_module}-opensource-src-%{version}.tar.xz

# header file to workaround multilib issue
# https://bugzilla.redhat.com/show_bug.cgi?id=1441343
Source5: qv4global_p-multilib.h

# support no_sse2 CONFIG (fedora i686 builds cannot assume -march=pentium4 -msse2 -mfpmath=sse flags, or the JIT that needs them)
# https://codereview.qt-project.org/#change,73710
Patch1: qtdeclarative-opensource-src-5.9.0-no_sse2.patch

# workaround for possible deadlock condition in QQuickShaderEffectSource
# https://bugzilla.redhat.com/show_bug.cgi?id=1237269
# https://bugs.kde.org/show_bug.cgi?id=348385
Patch2: qtdeclarative-QQuickShaderEffectSource_deadlock.patch

## upstream patches

## upstreamable patches

# https://bugs.kde.org/show_bug.cgi?id=346118#c108
Patch201: qtdeclarative-kdebug346118.patch

# https://codereview.qt-project.org/#/c/127354/
# https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=792594
Patch202: http://sources.debian.net/data/main/q/qtdeclarative-opensource-src/5.9.0~beta3-2/debian/patches/Do-not-make-lack-of-SSE2-support-on-x86-32-fatal.patch

%global __provides_exclude_from ^%{_qt5_archdatadir}/qml/.*\\.so$

Obsoletes: qt5-qtjsbackend < 5.2.0

BuildRequires: cmake
BuildRequires: qt5-qtbase-devel >= %{version}
BuildRequires: qt5-qtbase-private-devel
%{?_qt5:Requires: %{_qt5}%{?_isa} = %{_qt5_version}}
%if ! 0%{?bootstrap}
BuildRequires: qt5-qtxmlpatterns-devel
%endif
BuildRequires: python

%if 0%{?tests}
BuildRequires: dbus-x11
BuildRequires: mesa-dri-drivers
BuildRequires: time
BuildRequires: xorg-x11-server-Xvfb
%endif

%description
%{summary}.

%package devel
Summary: Development files for %{name}
Obsoletes: qt5-qtjsbackend-devel < 5.2.0
Provides:  %{name}-private-devel = %{version}-%{release}
Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: qt5-qtbase-devel%{?_isa}
%description devel
%{summary}.

%package static
Summary: Static library files for %{name}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
%description static
%{summary}.

%if 0%{?docs}
%package doc
Summary: API documentation for %{name}
License: GFDL
Requires: %{name} = %{version}-%{release}
BuildRequires: qt5-qdoc
BuildRequires: qt5-qhelpgenerator
# FTBS: same problem as qtbase
# BuildArch: noarch
%description doc
%{summary}.
%endif

%package examples
Summary: Programming examples for %{name}
Requires: %{name}%{?_isa} = %{version}-%{release}
%description examples
%{summary}.


%prep
%setup -q -n %{qt_module}-opensource-src-%{version}
%if 0%{?nosse2_hack}
%patch1 -p1 -b .no_sse2
%endif
%patch2 -p1 -b .QQuickShaderEffectSource_deadlock
%patch201 -p0 -b .kdebug346118
%patch202 -p1 -b .no_sse2_non_fatal


%build
%if 0%{?nosse2_hack}
# build libQt5Qml with no_sse2
mkdir -p %{_target_platform}-no_sse2
pushd    %{_target_platform}-no_sse2
%{qmake_qt5} -config no_sse2 ..
make sub-src-clean
make %{?_smp_mflags} -C src/qml
popd
%endif

# no shadow builds until fixed: https://bugreports.qt.io/browse/QTBUG-37417
%{qmake_qt5}

%if 0%{?docs}
make %{?_smp_mflags} docs
%endif

make %{?_smp_mflags}

%install
make install INSTALL_ROOT=%{buildroot}

%if 0%{?nosse2_hack}
mkdir -p %{buildroot}%{_qt5_libdir}/sse2
mv %{buildroot}%{_qt5_libdir}/libQt5Qml.so.5* %{buildroot}%{_qt5_libdir}/sse2/
make install INSTALL_ROOT=%{buildroot} -C %{_target_platform}-no_sse2/src/qml
%endif

%if 0%{?docs}
make install_docs INSTALL_ROOT=%{buildroot}
%endif

%ifarch %{multilib_archs}
# multilib: qv4global_p.h
  mv %{buildroot}%{_qt5_headerdir}/QtQml/%{version}/QtQml/private/qv4global_p.h \
     %{buildroot}%{_qt5_headerdir}/QtQml/%{version}/QtQml/private/qv4global_p-%{__isa_bits}.h
  install -p -m644 -D %{SOURCE5} %{buildroot}%{_qt5_headerdir}/QtQml/%{version}/QtQml/private/qv4global_p.h
%endif

# hardlink files to %{_bindir}, add -qt5 postfix to not conflict
mkdir %{buildroot}%{_bindir}
pushd %{buildroot}%{_qt5_bindir}
for i in * ; do
  case "${i}" in
    # qt4 conflicts
    qmlplugindump|qmlprofiler)
      ln -v  ${i} %{buildroot}%{_bindir}/${i}-qt5
      ln -sv ${i} ${i}-qt5
      ;;
    # qtchooser stuff
    qml|qmlbundle|qmlmin|qmlscene)
      ln -v  ${i} %{buildroot}%{_bindir}/${i}
      ln -v  ${i} %{buildroot}%{_bindir}/${i}-qt5
      ln -sv ${i} ${i}-qt5
      ;;
    *)
      ln -v  ${i} %{buildroot}%{_bindir}/${i}
      ;;
  esac
done
popd

## .prl/.la file love
# nuke .prl reference(s) to %%buildroot, excessive (.la-like) libs
pushd %{buildroot}%{_qt5_libdir}
for prl_file in libQt5*.prl ; do
  sed -i -e "/^QMAKE_PRL_BUILD_DIR/d" ${prl_file}
  rm -fv "$(basename ${prl_file} .prl).la"
  sed -i -e "/^QMAKE_PRL_LIBS/d" ${prl_file}
done
popd


%check
%if 0%{?tests}
export CTEST_OUTPUT_ON_FAILURE=1
export PATH=%{buildroot}%{_qt5_bindir}:$PATH
export LD_LIBRARY_PATH=%{buildroot}%{_qt5_libdir}
make sub-tests-all %{?_smp_mflags}
xvfb-run -a \
dbus-launch --exit-with-session \
time \
make check -k -C tests ||:
%endif


%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files
%license LICENSE.LGPL*
%{_qt5_libdir}/libQt5Qml.so.5*
%if 0%{?nosse2_hack}
%{_qt5_libdir}/sse2/libQt5Qml.so.5*
%endif
%{_qt5_libdir}/libQt5Quick.so.5*
%{_qt5_libdir}/libQt5QuickWidgets.so.5*
%{_qt5_libdir}/libQt5QuickParticles.so.5*
%{_qt5_libdir}/libQt5QuickTest.so.5*
%{_qt5_plugindir}/qmltooling/
%{_qt5_archdatadir}/qml/

%files devel
%{_bindir}/qml*
%{_qt5_bindir}/qml*
%{_qt5_headerdir}/Qt*/
%{_qt5_libdir}/libQt5Qml.so
%{_qt5_libdir}/libQt5Qml.prl
%{_qt5_libdir}/libQt5Quick*.so
%{_qt5_libdir}/libQt5Quick*.prl
%dir %{_qt5_libdir}/cmake/Qt5Quick*/
%{_qt5_libdir}/cmake/Qt5*/Qt5*Config*.cmake
%{_qt5_libdir}/pkgconfig/Qt5*.pc
%{_qt5_archdatadir}/mkspecs/modules/*.pri
%{_qt5_archdatadir}/mkspecs/features/*.prf
%dir %{_qt5_libdir}/cmake/Qt5Qml/
%{_qt5_libdir}/cmake/Qt5Qml/Qt5Qml_*Factory.cmake

%files static
%{_qt5_libdir}/libQt5QmlDevTools.a
%{_qt5_libdir}/libQt5QmlDevTools.prl
%{_qt5_libdir}/libQt5PacketProtocol.a
%{_qt5_libdir}/libQt5PacketProtocol.prl
%{_qt5_libdir}/libQt5QmlDebug.a
%{_qt5_libdir}/libQt5QmlDebug.prl

%if 0%{?docs}
%files doc
%license LICENSE.FDL
%{_qt5_docdir}/qtqml.qch
%{_qt5_docdir}/qtqml/
%{_qt5_docdir}/qtquick.qch
%{_qt5_docdir}/qtquick/

%files examples
%{_qt5_examplesdir}/
%endif


%changelog
* Fri Oct 06 2017 Jan Grulich <jgrulich@redhat.com> - 5.9.2-1
- Update to 5.9.2
  Resolves: bz#1482778

* Mon Sep 04 2017 Jan Grulich <jgrulich@redhat.com> - 5.9.1-2
- Enable documentation
  Resolves: bz#1482778

* Mon Aug 21 2017 Jan Grulich <jgrulich@redhat.com> - 5.9.1-1
- Update to 5.9.1
  Resolves: bz#1482778

* Wed Jan 11 2017 Jan Grulich <jgrulich@redhat.com> - 5.6.2-1
- Update to 5.6.2
  Resolves: bz#1384817

* Tue Aug 30 2016 Jan Grulich <jgrulich@redhat.com> - 5.6.1-10
- Increase build version to have newer version than in EPEL
  Resolves: bz#1317400

* Wed Jun 22 2016 Jan Grulich <jgrulich@redhat.com> - 5.6.1-3
- QML: Only release types if they aren't referenced anymore

* Wed Jun 15 2016 Jan Grulich <jgrulich@redhat.com> - 5.6.1-2
- Apply no_sse2 hack to all architecturs to make qt5-qtdeclarative-devel multilib-clean

* Wed Jun 08 2016 Jan Grulich <jgrulich@redhat.com> - 5.6.1-1
- Update to 5.6.1 + sync with Fedora
  Resolves: bz#1317400

* Wed Apr 13 2016 Jan Grulich <jgrulich@redhat.com> - 5.6.0-6
- Enable documentation
  Resolves: bz#1317400

* Thu Apr 07 2016 Jan Grulich <jgrulich@redhat.com> - 5.6.0-5
- Initial version for RHEL
  Resolves: bz#1317400

* Fri Mar 25 2016 Rex Dieter <rdieter@fedoraproject.org> - 5.6.0-4
- backport upstream fixes
- drop -fno-delete-null-pointer-checks hack (included in qt5-rpm-macros as needed now)

* Sat Mar 19 2016 Rex Dieter <rdieter@fedoraproject.org> - 5.6.0-3
- BR: cmake (cmake autoprovides)

* Fri Mar 18 2016 Rex Dieter <rdieter@fedoraproject.org> - 5.6.0-2
- rebuild

* Mon Mar 14 2016 Helio Chissini de Castro <helio@kde.org> - 5.6.0-1
- 5.6.0 final release

* Tue Feb 23 2016 Helio Chissini de Castro <helio@kde.org> - 5.6.0-0.11.rc
- Update to final RC

* Mon Feb 22 2016 Helio Chissini de Castro <helio@kde.org> - 5.6.0-0.10
- Update RC tarball from git

* Mon Feb 15 2016 Helio Chissini de Castro <helio@kde.org> - 5.6.0-0.9
- Update RC release

* Tue Feb 02 2016 Rex Dieter <rdieter@fedoraproject.org> 5.6.0-0.8.beta
- build with -fno-delete-null-pointer-checks to workaround gcc6-related runtime crashes (#1303643)

* Thu Jan 28 2016 Rex Dieter <rdieter@fedoraproject.org> 5.6.0-0.7.beta
- backport fix for older compilers (aka rhel6)

* Sun Jan 17 2016 Rex Dieter <rdieter@fedoraproject.org> 5.6.0-0.6.beta
- use %%license

* Mon Dec 21 2015 Rex Dieter <rdieter@fedoraproject.org> 5.6.0-0.5.beta
- fix Source URL, Release: tag

* Mon Dec 21 2015 Helio Chissini de Castro <helio@kde.org> - 5.6.0-0.4
- Update to final beta release

* Thu Dec 10 2015 Helio Chissini de Castro <helio@kde.org> - 5.6.0-0.3
- Official beta release

* Sun Dec 06 2015 Rex Dieter <rdieter@fedoraproject.org> 5.6.0-0.2
- de-bootstrap

* Tue Nov 03 2015 Helio Chissini de Castro <helio@kde.org> - 5.6.0-0.1
- Start to implement 5.6.0 beta, bootstrap

* Sat Oct 24 2015 Rex Dieter <rdieter@fedoraproject.org> 5.5.1-3
- workaround QQuickShaderEffectSource::updatePaintNode deadlock (#1237269, kde#348385)

* Thu Oct 15 2015 Helio Chissini de Castro <helio@kde.org> - 5.5.1-2
- Update to final release 5.5.1

* Tue Sep 29 2015 Helio Chissini de Castro <helio@kde.org> - 5.5.1-1
- Update to Qt 5.5.1 RC1

* Wed Jul 29 2015 Rex Dieter <rdieter@fedoraproject.org> 5.5.0-3
- -docs: BuildRequires: qt5-qhelpgenerator

* Thu Jul 16 2015 Rex Dieter <rdieter@fedoraproject.org> 5.5.0-2
- tighten qtbase dep (#1233829), .spec cosmetics

* Wed Jul 1 2015 Helio Chissini de Castro <helio@kde.org> 5.5.0-1
- New final upstream release Qt 5.5.0

* Mon Jun 29 2015 Helio Chissini de Castro <helio@kde.org> - 5.5.0-0.4.rc
- Second round of builds now with bootstrap enabled due new qttools

* Sat Jun 27 2015 Helio Chissini de Castro <helio@kde.org> - 5.5.0-0.3.rc
- Disable bootstrap

* Wed Jun 24 2015 Helio Chissini de Castro <helio@kde.org> - 5.5.0-0.2.rc
- Update for official RC1 released packages

* Mon Jun 08 2015 Rex Dieter <rdieter@fedoraproject.org> 5.4.2-2
- restore fix for QTBUG-45753/kde-345544 lost in 5.4.2 rebase

* Wed Jun 03 2015 Jan Grulich <jgrulich@redhat.com> 5.4.2-1
- 5.4.2

* Sat May 02 2015 Rex Dieter <rdieter@fedoraproject.org> 5.4.1-4
- pull in some upstream fixes, for QTBUG-45753/kde-345544 in particular

* Wed Apr 22 2015 Kevin Kofler <Kevin@tigcc.ticalc.org> - 5.4.1-3
- fix non-sse2 support (kde#346244) and optimize sse2 binaries

* Fri Feb 27 2015 Rex Dieter <rdieter@fedoraproject.org> - 5.4.1-2
- rebuild (gcc5)

* Tue Feb 24 2015 Jan Grulich <jgrulich@redhat.com> 5.4.1-1
- 5.4.1

* Mon Feb 16 2015 Rex Dieter <rdieter@fedoraproject.org> 5.4.0-3
- rebuild (gcc)

* Sat Feb 14 2015 Ville Skyttä <ville.skytta@iki.fi> - 5.4.0-2
- Fix cmake dir ownerhips

* Wed Dec 10 2014 Rex Dieter <rdieter@fedoraproject.org> 5.4.0-1
- 5.4.0 (final)

* Fri Nov 28 2014 Rex Dieter <rdieter@fedoraproject.org> 5.4.0-0.3.rc
- 5.4.0-rc

* Mon Nov 03 2014 Rex Dieter <rdieter@fedoraproject.org> 5.4.0-0.2.beta
- use new %%qmake_qt5 macro

* Sat Oct 18 2014 Rex Dieter <rdieter@fedoraproject.org> - 5.4.0-0.1.beta
- 5.4.0-beta
- %%ix84: drop sse2-optimized bits, need to rethink if/how to support it now

* Tue Sep 16 2014 Rex Dieter <rdieter@fedoraproject.org> 5.3.2-1
- 5.3.2

* Tue Sep 16 2014 Rex Dieter <rdieter@fedoraproject.org> 5.3.1-3
- -qt5 wrappers for qml qmlbundle qmlmin qmlscene

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 5.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Tue Jun 17 2014 Jan Grulich <jgrulich@redhat.com> - 5.3.1-1
- 5.3.1

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 5.3.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed May 21 2014 Jan Grulich <jgrulich@redhat.com> 5.3.0-1
- 5.3.0

* Wed Feb 05 2014 Rex Dieter <rdieter@fedoraproject.org> 5.2.1-1
- 5.2.1

* Sun Feb 02 2014 Marcin Juszkiewicz <mjuszkiewicz@redhat.com> 5.2.0-6
- Add AArch64 support (RHBUG: 1040452, QTBUG-35528)

* Mon Jan 27 2014 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-5
- build -examples only if supported

* Sun Jan 26 2014 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-4
- -examples subpkg

* Tue Jan 14 2014 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-3
- epel7 bootstrapped

* Mon Jan 06 2014 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-2
- BR: qt5-qtxmlpatterns-devel (#1048558)

* Thu Dec 12 2013 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-1
- 5.2.0

* Tue Dec 10 2013 Rex Dieter <rdieter@fedoraproject.org> - 5.2.0-0.12.rc1
- support out-of-src-tree builds
- %%ix86: install sse2/jit version to %%_qt5_libdir/sse2/

* Thu Dec 05 2013 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-0.11.rc1
- %%ix86: cannot assume sse2 (and related support) or the JIT that requires it...  disable.

* Mon Dec 02 2013 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-0.10.rc1
- 5.2.0-rc1

* Mon Nov 25 2013 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-0.5.beta1
- enable -doc only on primary archs (allow secondary bootstrap)

* Sat Nov 09 2013 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-0.4.beta1
- rebuild (arm/qreal)

* Thu Oct 24 2013 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-0.3.beta1
- 5.2.0-beta1

* Wed Oct 16 2013 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-0.2.alpha
- bootstrap ppc

* Tue Oct 01 2013 Rex Dieter <rdieter@fedoraproject.org> 5.2.0-0.1.alpha
- 5.2.0-alpha
- Obsoletes: qt5-qtjsbackend
- -doc subpkg

* Wed Aug 28 2013 Rex Dieter <rdieter@fedoraproject.org> 5.1.1-1
- 5.1.1

* Tue Aug 20 2013 Rex Dieter <rdieter@fedoraproject.org> 5.0.2-4
- qt5-qtjsbackend only supports ix86, x86_64 and arm

* Tue May 14 2013 Rex Dieter <rdieter@fedoraproject.org> 5.0.2-3
- fix qmlprofiler conflict with qt-creator

* Fri Apr 12 2013 Rex Dieter <rdieter@fedoraproject.org> 5.0.2-2
- fix qmlplugindump conflict with qt4-devel
- include license files, dist/changes*

* Thu Apr 11 2013 Rex Dieter <rdieter@fedoraproject.org> 5.0.2-1
- 5.0.2

* Sat Feb 23 2013 Rex Dieter <rdieter@fedoraproject.org> 5.0.1-1
- first try

