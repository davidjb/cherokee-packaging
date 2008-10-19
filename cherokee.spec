%define         home %{_var}/lib/%{name}
%define         shortversion %(echo %{version} | sed -e 's/\([0-9]*\.[0-9]*\)\.[0-9]*/\1/')

Name:           cherokee
Version:        0.8.1
Release:        2%{?dist}
Summary:        Flexible and Fast Webserver

Group:          Applications/Internet
License:        GPLv2
URL:            http://www.cherokee-project.com/
Source0:        http://www.cherokee-project.com/download/%{shortversion}/%{version}/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source1:        %{name}.init
Source2:        %{name}.logrotate

BuildRequires:  openssl-devel pam-devel pcre-devel mysql-devel
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
%configure \
    --with-wwwroot=%{_var}/www/%{name} \
    --enable-tls=openssl --enable-pthreads --enable-trace --disable-static
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
%{_bindir}/spawn-fcgi
%{_sbindir}/cherokee
%{_sbindir}/cherokee-admin
%{_sbindir}/cherokee-guardian
%{_libdir}/%{name}
%{_libdir}/lib%{name}-*.so.*
%{_datadir}/%{name}
# logs are written as root. no need to give perms to the cherokee user.
%dir %{_var}/log/%{name}/
%dir %attr(-,%{name},%{name}) %{_var}/lib/%{name}/
%doc AUTHORS ChangeLog COPYING INSTALL README TODO
%doc %{_datadir}/doc/%{name}
%doc %{_mandir}/man1/cget.1*
%doc %{_mandir}/man1/cherokee.1*
%doc %{_mandir}/man1/cherokee-tweak.1*
%doc %{_mandir}/man1/cherokee-admin.1*
%doc %{_mandir}/man1/cherokee-guardian.1*
%doc %{_mandir}/man1/spawn-fcgi.1*
%dir %{_var}/www/%{name}/
%dir %{_var}/www/%{name}/images/
%config(noreplace) %{_var}/www/%{name}/images/cherokee-logo.png
%config(noreplace) %{_var}/www/%{name}/images/default-bg.png
%config(noreplace) %{_var}/www/%{name}/images/powered_by_cherokee.png
%config(noreplace) %{_var}/www/%{name}/index.html

%files devel
%defattr(-,root,root,-)
%{_mandir}/man1/cherokee-config.1*
%{_bindir}/cherokee-config
##%{_includedir}/%{name}
%{_includedir}/%{name}/*.h
%{_libdir}/pkgconfig/%{name}.pc
%{_datadir}/aclocal/%{name}.m4
%{_libdir}/lib%{name}-*.so


%changelog
* Sun Sep 07 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.8.1-2
- corrections in spec
* Sun Sep 07 2008 Pavel Lisy <pavel.lisy@gmail.com> - 0.8.1-1
- first build
