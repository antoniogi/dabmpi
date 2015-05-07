PROGRAM calcula

  IMPLICIT NONE  

  INTEGER, PARAMETER :: n=3
  REAL, PARAMETER    :: pi=3.14159

  INTEGER i
  CHARACTER*100 line
  REAL R,a,B00,s,prefactor
  REAL dummy,cmul(n),iota,dchi,dpsi
  REAL d11(n),d11e(n),d11max,d11min
  REAL d31(n),d31e(n),d31max,d31min
  REAL eps32,eps32e,epseff(n),epseff_e(n)
  REAL*8 mean1,sd1,mean2,sd2

  OPEN(unit=1,file="../radius.dat",action='read')
  READ(1,*) R
  READ(1,*) a
  CLOSE(1)  

  OPEN(unit=1,file="b00.dat",action='read')
  READ(1,*) B00
  CLOSE(1)

  OPEN(unit=1,file="s.dat",action='read')
  READ(1,*) s
  CLOSE(1)

  OPEN(unit=1,file="results.data",action='read')
  READ(1,*) line
  READ(1,*) line
  DO i=1,n
    READ(1,*) cmul(i),dummy,dummy,dummy,d11min,d11max,d31min,d31max,dummy,dummy,dummy,dummy,dummy,dummy,dchi,dpsi,dummy,dummy
    iota=abs(dchi/dpsi)
    d11(i) =0.5*(d11min+d11max)
    d11e(i)=0.5*(d11min-d11max)
    d31(i) =0.5*(d31min+d31max)
    d31e(i)=0.5*sqrt(ABS((d31min-d31max)*(d11min-d11max)))
  END DO
  CLOSE(1)

  prefactor=8*R*iota*B00*B00/pi*(3*pi/4.)*(3.*pi/4.)*R/iota
  DO i=1,n
    eps32  =prefactor*d11(i) *cmul(i)
    eps32e =prefactor*d11e(i)*cmul(i)

    epseff(i)  =0.5*(eps32)**(2./3.)
    epseff_e(i)=epseff(i)*(eps32e/eps32)*(2./3.)
  END DO
  prefactor=-2.*1.46/3./iota/B00/(sqrt(sqrt(s)*a/R))
  d31 =d31 /prefactor
  d31e=d31e/prefactor

  OPEN(unit=2,file="results.dab",action='write')
  WRITE(2,*) ' cmul         epseff       epseff_e     d31         d31_e'
  DO i=1,n
   WRITE(2,100) cmul(i),epseff(i),epseff_e(i),d31(i),d31e(i)
  END DO
  mean1=SUM(epseff(1:n))/n
  mean2=SUM(d31(1:n))/n
  sd1=SQRT(SUM((epseff(1:n)-mean1)**2)/n) 
  sd2=SQRT(SUM((d31(1:n)   -mean2)**2)/n) 
!  sd1=0i
!  sd2=0
!  DO i=1,n
!    sd1=sd1+(epseff(i)-mean1)**2
!    print *,sd1,epseff(i),mean,(epseff(i)-mean1)**2
!    sd2=sd2+(d31(i)   -mean2)**2
!  END DO
!  sd1=sqrt(sd1/n)
!  sd2=sqrt(sd2/n)
  WRITE(2,101) '  average    ',mean1,sd1,mean2,sd2
  CLOSE(2)


100 FORMAT  (5(1pe13.5))
101 FORMAT  (a,4(1pe13.5))

END PROGRAM calcula

