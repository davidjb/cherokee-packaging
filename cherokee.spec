%define         home %{_var}/lib/%{name}
%define         shortversion %(echo %{version} | sed -e 's/\([0-9]*\.[0-9]*\)\.[0-9]*/\1/')
%define         is_el4 %(if [ "%{dist}" == ".el4" ] ; then echo true ; fi)
%define         is_el5 %(if [ "%{dist}" == ".el5" ] ; then echo true ; fi)
%if "%{is_el4}"
ExcludeArch:    ppc
%endif
%if "%{is_el5}"
ExcludeArch:    ppc
%endif

Name:           cherokee
Version:        0.99.20
Release:        1%{?dist}
Summary:        Flexible and Fast Webserver

Group:          Applications/Internet
License:        GPLv2
URL:            http://www.cherokee-project.com/
Source0:        http://www.cherokee-project.com/download/%{shortversion}/%{version}/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source1:        %{name}.init
Source2:        %{name}.logrotate

BuildRequires:  openssl-devel pam-devel mysql-devel pcre
# BuildRequires:  pcre-devel
BuildRequires:  gettext
# For spawn-fcgi
Requires:	    spawn-fcgi
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts

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
%setup -q

%build
%configure --with-wwwroot=%{_var}/www/%{name} --enable-tls=openssl --enable-pthreads --enable-trace --disable-static --disable-rpath
# Get rid of rpath
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
make %{?_smp_mflags}


%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}

%{__install} -d %{buildroot}%{_sysconfdir}/logrotate.d/
%{__install} -D -m 0644 pam.d_cherokee %{buildroot}%{_sysconfdir}/pam.d/%{name}
%{__install} -D -m 0755 %{SOURCE1}   %{buildroot}%{_sysconfdir}/init.d/%{name}
%{__install} -D -m 0644 %{SOURCE2}   %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -d %{buildroot}%{_var}/{log,lib}/%{name}/
%{__install} -d %{buildroot}%{_sysconfdir}/pki/%{name}

%{__sed} -i -e 's#log/%{name}\.access#log/%{name}/access_log#' \
            -e 's#log/%{name}\.error#log/%{name}/error_log#' \
            %{buildroot}%{_sysconfdir}/%{name}/cherokee.conf
%{__sed} -i -e 's#log/%{name}\.access#log/%{name}/access_log#' \
            -e 's#log/%{name}\.error#log/%{name}/error_log#' \
            %{buildroot}%{_sysconfdir}/%{name}/cherokee.conf.perf_sample

find  %{buildroot}%{_libdir} -name *.la -exec rm -rf {} \;
# put SSL certs to %{_sysconfdir}/pki/%{name}
rmdir %{buildroot}%{_sysconfdir}/%{name}/ssl

mv ChangeLog ChangeLog.iso8859-1
chmod -x COPYING
iconv -f ISO8859-1 -t UTF8 ChangeLog.iso8859-1 > ChangeLog

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

%preun
if [ $1 = 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi

%post
/sbin/ldconfig
/sbin/chkconfig --add %{name}

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%{_sysconfdir}/init.d/%{name}
%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/pki/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/cherokee.conf
%config(noreplace) %{_sysconfdir}/%{name}/cherokee.conf.perf_sample
%config(noreplace) %{_sysconfdir}/pam.d/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_bindir}/cget
%{_bindir}/cherokee-panic
%{_bindir}/cherokee-tweak
# %%{_bindir}/spawn-fcgi
%{_sbindir}/cherokee
%{_sbindir}/cherokee-admin
%{_sbindir}/cherokee-worker
%{_libdir}/%{name}
%{_libdir}/lib%{name}-*.so.*
%{_datadir}/locale/*/LC_MESSAGES/cherokee.mo
%{_datadir}/%{name}
# logs are written as root. no need to give perms to the cherokee user.
%dir %{_var}/log/%{name}/
%dir %attr(-,%{name},%{name}) %{_var}/lib/%{name}/
%doc AUTHORS ChangeLog COPYING INSTALL README
%doc %{_datadir}/doc/%{name}
%doc %{_mandir}/man1/cget.1*
%doc %{_mandir}/man1/cherokee.1*
%doc %{_mandir}/man1/cherokee-tweak.1*
%doc %{_mandir}/man1/cherokee-admin.1*
%doc %{_mandir}/man1/cherokee-worker.1*
# %%doc %{_mandir}/man1/spawn-fcgi.1*
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
* Sat Jul 11 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.20-1
- updated to 0.99.20

* Sun Jun 14 2009 Pavel Lisy <pavel.lisy@gmail.com> - 0.99.17-2
- .spec changes in %files section

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
