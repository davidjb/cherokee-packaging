%define         home %{_var}/lib/%{name}
%define         shortversion   %(echo %{version} | sed -r 's/\.[0-9]+$//g')
%define         opensslversion 1.0.0d
%{!?_unitdir:%define _unitdir /lib/systemd/system}

Name:           cherokee
Version:        1.2.102
Release:        1%{?dist}
Summary:        Flexible and Fast Webserver

Group:          Applications/Internet
License:        GPLv2
URL:            http://www.cherokee-project.com/
#Source0:        http://www.cherokee-project.com/download/%{shortversion}/%{version}/%{name}-%{version}.tar.gz
Source0:        http://www.hpc.jcu.edu.au/sources/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source1:        %{name}.init
Source2:        %{name}.logrotate
Source3:        %{name}.service
%if "%{dist}" == ".el4" || "%{dist}" == ".el5"
Source100:      http://www.openssl.org/source/openssl-%{opensslversion}.tar.gz
%endif

# Drop privileges to cherokee:cherokee after startup
Patch0: 01-drop-privileges.patch

BuildRequires:  pam-devel mysql-devel pcre GeoIP-devel openldap-devel
%if "%{dist}" == ".el4"
BuildRequires:  php
%else
BuildRequires:  php-cli
%endif
# BuildRequires:  pcre-devel
BuildRequires:  gettext
# For spawn-fcgi
Requires:        spawn-fcgi

%if "%{dist}" == ".fc15" || "%{dist}" == ".fc16" || "%{dist}" == ".fc17"
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
%else
Requires(post):  chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
%endif

Provides: webserver

%description
Cherokee is a very fast, flexible and easy to configure Web Server. It supports
the widespread technologies nowadays: FastCGI, SCGI, PHP, CGI, TLS and SSL
encrypted connections, Virtual hosts, Authentication, on the fly encoding,
Apache compatible log files, and much more.

%package devel
Group:         Development/Libraries
Summary:       Development files of cherokee
Requires:      %{name} = %{version}
%description devel
Cherokee is a very fast, flexible and easy to configure Web Server. It supports
the widespread technologies nowadays: FastCGI, SCGI, PHP, CGI, TLS and SSL
encrypted connections, Virtual hosts, Authentication, on the fly encoding,
Apache compatible log files, and much more.

This package holds the development files for cherokee.


%prep
%if "%{dist}" == ".el4" || "%{dist}" == ".el5"
%setup -q -a 100
%else
%setup -q
%endif
%patch0 -p1 -b .privs

%build
%if "%{dist}" == ".el4" || "%{dist}" == ".el5"
pushd openssl-%{opensslversion}
./config --prefix=/usr --openssldir=%{_sysconfdir}/pki/tls shared
RPM_OPT_FLAGS="$RPM_OPT_FLAGS -Wa,--noexecstack"
make depend
make all
mkdir ./lib
for lib in *.a ; do
  ln -s ../$lib ./lib
done
popd
%endif

%configure --with-wwwroot=%{_var}/www/%{name} \
%if "%{dist}" == ".el4" || "%{dist}" == ".el5"
   --with-libssl=$(pwd)/openssl-%{opensslversion} --enable-static-module=libssl \
%else
   --with-libssl \
%endif
   --disable-static
# Get rid of rpath
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
make %{?_smp_mflags}


%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}

%{__install} -d %{buildroot}%{_sysconfdir}/logrotate.d/
%{__install} -D -m 0644 pam.d_cherokee %{buildroot}%{_sysconfdir}/pam.d/%{name}
%{__install} -D -m 0644 %{SOURCE2}   %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -d %{buildroot}%{_var}/{log,lib}/%{name}/
%{__install} -d %{buildroot}%{_sysconfdir}/pki/%{name}
%if "%{dist}" == ".fc15" || "%{dist}" == ".fc16" || "%{dist}" == ".fc17"
%{__install} -d %{buildroot}%{_unitdir}
%{__install} -D -m 0644 %{SOURCE3}   %{buildroot}%{_unitdir}/%{name}.service
%else
%{__install} -D -m 0755 %{SOURCE1}   %{buildroot}%{_sysconfdir}/init.d/%{name}
%endif

%{__sed} -i -e 's#log/%{name}\.access#log/%{name}/access_log#' \
            -e 's#log/%{name}\.error#log/%{name}/error_log#' \
            %{buildroot}%{_sysconfdir}/%{name}/cherokee.conf
%{__sed} -i -e 's#log/%{name}\.access#log/%{name}/access_log#' \
            -e 's#log/%{name}\.error#log/%{name}/error_log#' \
            %{buildroot}%{_sysconfdir}/%{name}/cherokee.conf.perf_sample

touch %{buildroot}%{_var}/log/%{name}/access_log \
      %{buildroot}%{_var}/log/%{name}/error_log

find  %{buildroot}%{_libdir} -name *.la -exec rm -rf {} \;

#mv ChangeLog ChangeLog.iso8859-1
chmod -x COPYING
#iconv -f ISO8859-1 -t UTF8 ChangeLog.iso8859-1 > ChangeLog

# Get rid of spawn-fcgi bits, they conflict with the lighttpd-fastcgi package
# but are otherwise identical.
rm -rf %{buildroot}%{_bindir}/spawn-fcgi
rm -rf %{buildroot}%{_mandir}/man1/spawn-fcgi.*


%clean
rm -rf %{buildroot}


%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
useradd -r -g %{name} -d %{home} -s /sbin/nologin \
   -c "%{name} web server" %{name}
exit 0

%post
%if "%{dist}" == ".fc15" || "%{dist}" == ".fc16" || "%{dist}" == ".fc17"
if [ $1 -eq 1 ] ; then 
    # Initial installation: enabled by default
    /bin/systemctl enable cherokee.service >/dev/null 2>&1 || :
fi
%else
/sbin/ldconfig
/sbin/chkconfig --add %{name}
%endif

%preun
%if "%{dist}" == ".fc15" || "%{dist}" == ".fc16" || "%{dist}" == ".fc17"
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable cherokee.service > /dev/null 2>&1 || :
    /bin/systemctl stop cherokee.service > /dev/null 2>&1 || :
fi
%else
if [ $1 = 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi
%endif

%postun
%if "%{dist}" == ".fc15" || "%{dist}" == ".fc16" || "%{dist}" == ".fc17"
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart cherokee.service >/dev/null 2>&1 || :
fi
%else
/sbin/ldconfig
%endif

%files
%defattr(-,root,root,-)
%if "%{dist}" == ".fc15" || "%{dist}" == ".fc16" || "%{dist}" == ".fc17"
%{_unitdir}/%{name}.service
%else
%{_sysconfdir}/init.d/%{name}
%endif
%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/pki/%{name}
%attr(0644,%{name},%{name}) %config(noreplace) %{_sysconfdir}/%{name}/cherokee.conf
%attr(0644,%{name},%{name}) %config(noreplace) %{_sysconfdir}/%{name}/cherokee.conf.perf_sample
%config(noreplace) %{_sysconfdir}/pam.d/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_bindir}/cget
%{_bindir}/cherokee-panic
%{_bindir}/cherokee-tweak
%{_bindir}/cherokee-admin-launcher
%{_bindir}/cherokee-macos-askpass
%{_bindir}/CTK-run
# %%{_bindir}/spawn-fcgi
%{_sbindir}/cherokee
%{_sbindir}/cherokee-admin
%{_sbindir}/cherokee-worker
%{_libdir}/%{name}
%{_libdir}/lib%{name}-*.so.*
%{_datadir}/locale/*/LC_MESSAGES/cherokee.mo
%{_datadir}/%{name}
## Since we drop privileges to cherokee:cherokee, change permissions on these
# log files.
%attr(-,%{name},%{name}) %dir %{_var}/log/%{name}/
%attr(-,%{name},%{name}) %{_var}/log/%{name}/error_log
%attr(-,%{name},%{name}) %{_var}/log/%{name}/access_log
%attr(-,%{name},%{name}) %dir %{_var}/lib/%{name}/
%doc AUTHORS COPYING 
%doc %{_datadir}/doc/%{name}
%doc %{_mandir}/man1/cget.1*
%doc %{_mandir}/man1/cherokee.1*
%doc %{_mandir}/man1/cherokee-tweak.1*
%doc %{_mandir}/man1/cherokee-admin.1*
%doc %{_mandir}/man1/cherokee-worker.1*
%doc %{_mandir}/man1/cherokee-admin-launcher.1*
# doc {_mandir}/man1/spawn-fcgi.1*
%dir %{_var}/www/
%dir %{_var}/www/%{name}/
%dir %{_var}/www/%{name}/images/
%config(noreplace) %{_var}/www/%{name}/images/cherokee-logo.png
%config(noreplace) %{_var}/www/%{name}/images/default-bg.png
%config(noreplace) %{_var}/www/%{name}/images/powered_by_cherokee.png
%config(noreplace) %{_var}/www/%{name}/images/favicon.ico
%config(noreplace) %{_var}/www/%{name}/index.html

%files devel
%defattr(-,root,root,-)
%{_mandir}/man1/cherokee-config.1*
%{_bindir}/cherokee-config
%dir %{_includedir}/%{name}/
%{_includedir}/%{name}/*.h
%{_libdir}/pkgconfig/%{name}.pc
%{_datadir}/aclocal/%{name}.m4
%{_libdir}/lib%{name}-*.so

%changelog
* Wed Oct 19 2011 Pavel Lisý <pali@fedoraproject.org> - 1.2.101-1
- Latest 1.2.x upstream release

* Tue Oct 18 2011 Pavel Lisý <pali@fedoraproject.org> - 1.2.100-2
- Resolves bz 746532 - put some deps back: GeoIP-devel openldap-devel

* Mon Oct 10 2011 Pavel Lisý <pali@fedoraproject.org> - 1.2.100-1
- Latest 1.2.x upstream release
- .spec corrections for optional build for systemd
- Resolves bz 710474
- Resolves bz 713307
- Resolves bz 680691

* Wed Sep 14 2011 Pavel Lisý <pali@fedoraproject.org> - 1.2.99-2
- .spec corrections for EL4 build

* Sat Sep 10 2011 Pavel Lisý <pali@fedoraproject.org> - 1.2.99-1
- Latest 1.2.x upstream release
- Resolves bz 713306
- Resolves bz 710473
- Resolves bz 728741
- Resolves bz 720515
- Resolves bz 701196
- Resolves bz 712555

* Wed Aug 10 2011 Pavel Lisý <pali@fedoraproject.org> - 1.2.98-1
- Latest 1.2.x upstream release

* Wed Mar 23 2011 Dan Horák <dan@danny.cz> - 1.2.1-2
- rebuilt for mysql 5.5.10 (soname bump in libmysqlclient)

* Fri Feb 22 2011 Pavel Lisý <pali@fedoraproject.org> - 1.2.1-1
- Resolves bz 678243
- Resolves bz 680051
- Resolves bz 678838 (EPEL)
- Resolves bz 622514 (EPEL)

* Fri Feb 22 2011 Pavel Lisý <pali@fedoraproject.org> - 1.0.20-4
- Resolves bz 570317

* Tue Feb 22 2011 Pavel Lisý <pali@fedoraproject.org> - 1.0.20-3
- reenabled ppc build for el4/el5

* Tue Feb 22 2011 Pavel Lisý <pali@fedoraproject.org> - 1.0.20-2
- .spec corrections for el4

* Tue Feb 22 2011 Pavel Lisý <pali@fedoraproject.org> - 1.0.20-1
- Latest 1.0.x upstream release (1.0.20)
- Resolves bz 657085
- Resolves bz 678237

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Sep  1 2010 Lorenzo Villani <lvillani@binaryhelix.net> - 1.0.8-2
- Merge changes to cherokee.init from Pavel Lisý (hide cherokee's
  stdout messages)

* Sun Aug 29 2010 Lorenzo Villani <lvillani@binaryhelix.net> - 1.0.8-1
- New upstream release (1.0.8)
- Init script overhaul
- Relevant changes since 1.0.6:
- NEW: Enhanced 'Header' rule match
- NEW: Improved extensions rule
- FIX: SSL/TLS works with Firefox again
- FIX: Better SSL/TLS connection close
- FIX: Range requests work better now
- FIX: Hot-linking wizard w/o Referer
- FIX: Hot-linking wizard usability
- FIX: Minor CSS fix in the default dirlist theme
- FIX: POST management issue
- FIX: PHP wizard, better configuration
- FIX: admin, unresponsive button
- DOC: Misc improvements
- i18n: French translation updated

* Fri Aug 6 2010 Lorenzo Villani <lvillani@enterprise.binaryhelix.net> 1.0.6-1
- Relevant changes since 1.0.4
- NEW: Much better UTF-8 encoding
- NEW: Templates support slicing now (as in Python str)
- NEW: 'TLS/SSL' matching rule
- NEW: Reverse HTTP proxy can overwrite "Expire:" entries
- NEW: Redirection handler support the ${host} macro now
- FIX: POST support in the HTTP reverse proxy
- FIX: Some SSL/TLS were fixed. [unfinished]
- FIX: X-Forwarded-For parsing bug fixed
- FIX: Better php-fpm support in the PHP wizard
- FIX: Bundled PySCGI bumped to 1.14
- FIX: Random 100% CPU usage
- FIX: POST management regression in the proxy
- FIX: Connection RST/WAIT_FIN related fixes
- FIX: Dirlist bugfix: symbolic links handling
- FIX: POST status report bug-fixes
- DOC: Documentation updates
- i18n: Spanish translation updated
- i18n: Dutch translation updated
- i18n: Polish translation updated
- i18n: German translation updated

* Mon Jun 28 2010 Lorenzo Villani <lvillani@binaryhelix.net> - 1.0.4-1
- Relevant changes since 1.0.0
- OLD: Dropped support for RFC 2817.
- NEW: MediaWiki wizard
- NEW: PHP wizard for Virtual Servers
- FIX: Fixes a regression in the SSL/TLS support
- FIX: Shorter SSL session names
- FIX: Content-Range management issue
- FIX: Content-Type (max-age) management issue fixed
- FIX: Better 'IPv6 is missing' report
- FIX: RRD for VServers with spaces in the name
- FIX: admin, Fixes uWSGI wizard
- FIX: admin, Adds extra path to find php-fpm
- FIX: admin, Fixes the Static content wizard
- FIX: admin, Fixes issue with the RoR wizard
- FIX: admin, Validation of executable files
- FIX: HTTP error codes bug
- FIX: Auth headers are added from error pages if needed
- FIX: Better fd limit management
- FIX: Duplicated Cache-Control header
- FIX: Safer TLS/SSL close.
- FIX: Trac wizard checking bug.
- FIX: NCSA/Combined log invalid length.
- FIX: Better inter-wizard dependencies management
- FIX: PID file management fix
- FIX: PHP wizard create functional vservers now
- FIX: Add WebM MIME types
- FIX: Admin, rule table style improved
- FIX: Reordering for vservers and rules
- FIX: Joomla wizard
- FIX: Validation for incoming ports/interfaces
- FIX: Regression: Document root can be defined per-rule
- FIX: 'Broken installation detected' error improved
- FIX: Handler common parameters work again
- FIX: PHP-fpm detection
- FIX: Better list validations
- FIX: File exists issue
- DOC: Various updates
- I18n: Spanish translation updated
- I18n: Brazilian Portuguese translation updated
- I18n: Polish updated
- I18n: Dutch updated
- I18n: New translation to Catalan

* Wed May 12 2010 Lorenzo Villani <lvillani@binaryhelix.net> - 1.0.0-1
- First stable release

* Wed May  5 2010 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.49-1
- Changes since 0.99.44:
- New cherokee-admin (rewritten from scratch)
- FIX: Reverse proxy bug
- FIX: Handler init bug: crashed on ARM
- FIX: Adds missing HTTP methods
- FIX: PTHREAD_RWLOCK_INITIALIZER usage
- FIX: uWSGI paths bug
- FIX: WordPress wizard bug
- FIX: Safer (synchronous) cherokee-admin start
- FIX: Keep-alive related bug
- FIX: Error log management has been fixed
- FIX: Re-integrates the phpMyAdmin wizard
- FIX: Cherokee-admin default timeout increased
- FIX: Wordpress wizard
- FIX: Flags in the GeoIP plug-in
- FIX: LOCK method detection
- FIX: upgrade_config.py was broken
- I18n: Chinese translation updated
- I18n: New translation to Polish
- I18n: Spanish translation updated
- I18n: Dutch translation updated
- DOC: Improves Server Info handler documentation
- DOC: Many documentation updates
- DOC: New screenshots
- DOC: PHP recipe improved

* Fri Apr 23 2010 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.44-1
- FIX: Large POST support bug fixed
- FIX: UTF-8 requests bug fixed
- FIX: 7z MIME-type
- FIX: Added missing HTTP response codes
- FIX: Added missing HTTP methods
- FIX: Many documentation typos fixed
- I18N: Dutch translation updated

* Thu Mar 18 2010 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.43-1
- 0.99.43
- FIX: Performance related regression (Keep-alive w/o cache)
- FIX: Better lingering close
- FIX: PAM authentication module fixes: threading issue
- FIX: Cherokee-admin supports IPv6 by default
- FIX: Parsing IPv6 addresses in "allow from" restrictions
- FIX: Rule OR is slightly faster now
- FIX: Fixes a few accessibility issues in cherokee-admin
- FIX: Symfony wizard, fixed to use the new paths
- suppressed confusing output from init script

* Tue Feb 2 2010 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.42-1
- 0.99.42
- Compilation and last-minute fixes
- NEW: POST managing subsystem has been rewritten from scratch
- NEW: New POST (uploads) status reporting mechanism
- NEW: Rules can be configured to forbid the use of certain encoders
- NEW: Custom logger: Adds ${response_size} support
- FIX: File descriptor leak fixed in the HTTP reverse proxy
- FIX: Error pages with UTF8 encoded errors work now
- FIX: Safer file descriptor closing
- FIX: getpwuid_r() detection
- FIX: Original query strings (and requests) are logged now
- FIX: Misc cherokee-admin fixes
- FIX: uWSCGI: Endianess fixes and protocol modifiers
- FIX: Chinese translation updated
- FIX: Cherokee-admin: Display custom error if the doc. is missing
- FIX: Early logging support is not supported any longer
- FIX: QA and Cherokee-Admin: Bumps PySCGI to version 1.11
- FIX: The 'fastcgi' handler has been deprecated in favor of 'fcgi'
- FIX: PATH_INFO generation on merging non-final rules (corner case)
- DOC: Installation updated

* Tue Dec 29 2009 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.39-1
- 0.99.39

* Mon Dec 28 2009 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.38-1
- 0.99.38

* Wed Dec 23 2009 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.37-1
- 0.99.37

* Thu Dec  3 2009 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.31-1
- New upstream release: 0.99.31

* Tue Dec  1 2009 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.30-1
- 0.99.30

* Sun Nov 22 2009 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.29-1
- 0.99.29

* Sat Nov 07 2009 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.27-1
- 0.99.27

* Sat Sep  5 2009 Lorenzo Villani <lvillani@binaryhelix.net> - 0.99.24-1
- 0.99.24

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 0.99.20-3
- rebuilt with new openssl

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.99.20-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sat Jul 11 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.20-1
- updated to 0.99.20

* Sun Jun 14 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.17-2
- .spec changes in files section

* Sun Jun 14 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.17-1
- updated to 0.99.17

* Tue Apr 21 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.11-2
- added BuildRequires: gettext

* Mon Apr 20 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.11-1
- updated to 0.99.11

* Sat Mar 07 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.0-1
- updated to 0.99.0

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.98.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Feb 16 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.98.1-1
- updated to 0.98.1

* Sat Jan 24 2009 Caolán McNamara <caolanm@redhat.com> - 0.11.6-2
- rebuild for dependencies

* Tue Dec 30 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.11.6-1
- Resolves bz 478488, updated to 0.11.6

* Tue Dec 30 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.11.2-4
- Resolves bz 472749 and 472747, changed Requires: spawn-fcgi

* Tue Dec 16 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.11.2-3
- ppc arch excluded only for el4

* Tue Dec 16 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.11.2-2
- ppc arch excluded

* Tue Dec 16 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.11.2-1
- updated to 0.11.2

* Tue Dec 16 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.10.0-3
- Unowned directories, Resolves bz 474634

* Thu Nov  6 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 0.10.0-2
- do not package spawn-fcgi files (lighttpd-fastcgi provides them)
  Resolves bz 469947
- get rid of rpath in compiled files

* Fri Oct 31 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.10.0-1
- updated to 0.10.0

* Sun Sep 07 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.8.1-2
- corrections in spec

* Sun Sep 07 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.8.1-1
- first build
