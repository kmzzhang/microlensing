import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from function_numpy import search,search_first_postion
import sys
from matplotlib import colors
import time
#实现自适应采点算法
#首先将轨道与同一点的采样分开
#其次将theta与contour采样绑定
#实现误差计算
#实现自适应采点算法
sys.setrecursionlimit(10000)
np.seterr(divide='ignore', invalid='ignore')
class model():#initialize parameter
    def __init__(self,par):
        self.solve_time=0
        self.t_0=par['t_0']
        self.u_0=par['u_0']
        self.t_E=par['t_E']
        self.rho=par['rho']
        self.q=par['q']
        self.s=par['s']
        self.alpha_deg=par['alpha_deg']
        self.alpha_rad=par['alpha_deg']*2*np.pi/360
        self.times=(par['times']-self.t_0)/self.t_E
        self.trajectory_n=len(self.times)
        self.m1=1/(1+self.q)
        self.m2=self.q/(1+self.q)
        self.trajectory_l=self.get_trajectory_l()
    def to_centroid(self,x):#change coordinate system to cetorid
        delta_x=self.s/(1+self.q)
        return -(np.conj(x)-delta_x)
    def to_lowmass(self,x):#change coordinaate system to lowmass
        delta_x=self.s/(1+self.q)
        return -np.conj(x)+delta_x
    def get_trajectory_l(self):
        alpha=self.alpha_rad
        b=self.u_0
        trajectory_c=np.array([i*np.cos(alpha)-b*np.sin(alpha)+1j*(b*np.cos(alpha)+i*np.sin(alpha)) for i in self.times])
        trajectory_l=self.to_lowmass(trajectory_c)
        return trajectory_l
    def get_zeta_l(self,trajectory_centroid_l,theta):#获得等高线采样的zeta
        rho=self.rho
        rel_centroid=rho*np.cos(theta)+1j*rho*np.sin(theta)
        zeta_l=trajectory_centroid_l+rel_centroid
        return zeta_l
    def get_poly_coff(self,zeta_l):
        s=self.s
        m2=self.m2
        zeta_conj=np.conj(zeta_l)
        c0=s**2*zeta_l*m2**2
        c1=-s*m2*(2*zeta_l+s*(-1+s*zeta_l-2*zeta_l*zeta_conj+m2))
        c2=zeta_l-s**3*zeta_l*zeta_conj+s*(-1+m2-2*zeta_conj*zeta_l*(1+m2))+s**2*(zeta_conj-2*zeta_conj*m2+zeta_l*(1+zeta_conj**2+m2))
        c3=s**3*zeta_conj+2*zeta_l*zeta_conj+s**2*(-1+2*zeta_conj*zeta_l-zeta_conj**2+m2)-s*(zeta_l+2*zeta_l*zeta_conj**2-2*zeta_conj*m2)
        c4=zeta_conj*(-1+2*s*zeta_conj+zeta_conj*zeta_l)-s*(-1+2*s*zeta_conj+zeta_conj*zeta_l+m2)
        c5=(s-zeta_conj)*zeta_conj
        coff=np.stack((c5,c4,c3,c2,c1,c0),axis=1)
        return coff
    def image_match(self,solution):#roots in lowmass coordinate
        sample_n=solution.sample_n;theta=solution.theta;roots=solution.roots;parity=solution.parity;roots_is_create=solution.Is_create
        theta_map=[];uncom_theta_map=[];uncom_sol_num=[];sol_num=[];uncom_curve=[];curve=[];parity_map=[];uncom_parity_map=[]
        roots_non_nan=np.isnan(roots).sum(axis=0)==0
        roots_first_eq_last=np.isclose(roots[0,:],roots[-1,:],rtol=1e-6)
        complete_cond=(roots_non_nan&roots_first_eq_last)
        uncomplete_cond=(roots_non_nan&(~roots_first_eq_last))
        curve+=list(roots[:,complete_cond].T)
        theta_map+=[theta]*np.sum(complete_cond);sol_num+=list(roots_is_create[:,complete_cond].T);parity_map+=list(parity[:,complete_cond].T)
        flag=0;flag2=0
        if uncomplete_cond.any():
            flag2=1
            uncom_curve+=list(roots[:,uncomplete_cond].T)
            uncom_theta_map+=[theta]*np.sum(uncomplete_cond)
            uncom_sol_num+=list(roots_is_create[:,uncomplete_cond].T)
            uncom_parity_map+=list(parity[:,uncomplete_cond].T)
        if ((np.isnan(roots).sum(axis=0)!=sample_n)&(~roots_non_nan)).any():
            flag=1
            temp_idx=np.where((np.isnan(roots).sum(axis=0)!=sample_n)&(~roots_non_nan))[0]#the arc crossing caustic we store it to temp
        if flag:##split all roots with nan and caulcate mag
            temp_roots=roots[:,temp_idx]
            temp_Is_create=roots_is_create[:,temp_idx]
            temp_parity=parity[:,temp_idx]
            real_parity=np.copy(temp_parity)
            while np.shape(temp_idx)[0]!=0:
                initk,initm,temp_parity=search_first_postion(temp_roots,temp_parity)
                if temp_parity[initk,initm]==1:
                    temp_parity*=-1
                roots_c=np.copy(temp_roots)
                m_map,n_map,temp_roots,temp_parity=search([initk],[initm],temp_roots,temp_parity,temp_roots[initk,initm],temp_Is_create)
                if (initk!=0)&(initk!=-1):
                    m_map+=[m_map[0]]
                    n_map+=[n_map[0]]
                temp_curve=roots_c[m_map,n_map];temp_cur_theta_map=theta[m_map];temp_parity_map=real_parity[m_map,n_map]
                plt.plot(temp_curve.real,temp_curve.imag)
                #np.savetxt('result/curve.txt',temp_curve,delimiter=',',fmt='%.4f')
                plt.show()
                temp_cur_num_map=temp_Is_create[m_map,n_map]
                temp_idx=np.where((~np.isnan(temp_roots)).any(axis=0))[0]
                temp_roots=temp_roots[:,temp_idx];temp_parity=temp_parity[:,temp_idx];temp_Is_create=temp_Is_create[:,temp_idx];real_parity=real_parity[:,temp_idx]
                if np.isclose(temp_curve[0],temp_curve[-1],rtol=1e-6):
                    curve+=[temp_curve];theta_map+=[temp_cur_theta_map];sol_num+=[temp_cur_num_map];parity_map+=[temp_parity_map]
                else:
                    uncom_curve+=[temp_curve];uncom_theta_map+=[temp_cur_theta_map];uncom_sol_num+=[temp_cur_num_map];uncom_parity_map+=[temp_parity_map]
                    flag2=1
        if flag2:#flag2 is the uncompleted arc so we store it to uncom_curve
            if len(uncom_curve)!=0:
                arc=uncom_curve[0]
                arc_theta=uncom_theta_map[0]
                arc_num=uncom_sol_num[0]
                arc_parity=uncom_parity_map[0]
                length=len(uncom_curve)-1
                while length>0:
                    for k in range(1,len(uncom_curve)):
                        tail=arc[-1]
                        head=uncom_curve[k][0]
                        if np.isclose(tail,head,rtol=1e-6):
                            arc=np.append(arc,uncom_curve[k][1:])
                            arc_theta=np.append(arc_theta,uncom_theta_map[k][1:])
                            arc_num=np.append(arc_num,uncom_sol_num[k][1:])
                            arc_parity=np.append(arc_parity,uncom_parity_map[k][1:])
                            length-=1
                        else:
                            head=uncom_curve[k][-1]
                            if np.isclose(tail,head,rtol=1e-6):
                                arc=np.append(arc,uncom_curve[k][-1::-1][1:])
                                arc_theta=np.append(arc_theta,uncom_theta_map[k][-1::-1][1:])
                                arc_num=np.append(arc_num,uncom_sol_num[k][-1::-1][1:])
                                arc_parity=np.append(arc_parity,uncom_parity_map[k][-1::-1][1:])
                                length-=1
                curve+=[arc]
                theta_map+=[arc_theta]
                sol_num+=[arc_num]
                parity_map+=[arc_parity]
        return curve,theta_map,sol_num,parity_map
    def get_magnifaction(self,tol):
        epsilon=tol
        trajectory_l=self.trajectory_l
        trajectory_n=self.trajectory_n
        mag_curve=[]
        image_contour_all=[]
        add_list=[]
        for i in range(trajectory_n):
            sample_n=100;theta_init=np.linspace(0,2*np.pi,sample_n,dtype=np.float128)
            error_tot=np.ones(1);error_hist=np.ones(1)
            print(i)
            if i==140:
                print(140)
            else:
                continue
            while ((error_hist>epsilon/np.sqrt(sample_n)).any()):#多点采样但精度不同
            #while ((error_tot>epsilon).any()):
                mag=0
                if np.shape(error_hist)[0]==1:#第一次采样
                    error_hist=np.zeros_like(theta_init)
                    theta_init=np.linspace(0,2*np.pi,sample_n,dtype=np.float128)
                    zeta_l=self.get_zeta_l(trajectory_l[i],theta_init).astype(np.complex128)
                    coff=self.get_poly_coff(zeta_l)
                    solution=Solution(self.q,self.s,zeta_l,coff,theta_init)
                    test=0
                else:#自适应采点插入theta
                    if 0:#单区间多点采样
                        idx=np.array([np.argmax(error_hist)]).reshape(1)
                        add_number=np.ceil((error_hist[idx]/epsilon*np.sqrt(sample_n))**0.2).astype(int)+1
                        add_theta=[np.linspace(theta_init[idx[i]-1],theta_init[idx[i]],add_number[i],endpoint=False)[1:] for i in range(np.shape(idx)[0])]
                    if 0:#单区间单点采样
                        idx=np.array([np.argmax(error_hist)]).reshape(1)
                        add_number=np.array([1])+1
                        add_theta=[np.linspace(theta_init[idx[i]-1],theta_init[idx[i]],add_number[i],endpoint=False)[1:] for i in range(np.shape(idx)[0])]
                    if 0:#多区间单点采样
                        idx=np.where(error_hist>(epsilon/sample_n))[0]#不满足要求的点
                        add_number=np.ones_like(idx)+1
                        #add_number=np.ceil((error_hist[idx]/epsilon*np.sqrt(sample_n))**0.2).astype(int)+1
                        add_theta=[np.linspace(theta_init[idx[i]-1],theta_init[idx[i]],add_number[i],endpoint=False)[1:] for i in range(np.shape(idx)[0])]
                    if 0:#多区间多点采样
                        idx=np.where(error_hist>(epsilon/sample_n))[0]#不满足要求的点
                        add_number=np.ceil((error_hist[idx]/epsilon*np.sqrt(sample_n))**0.2).astype(int)+1#至少要插入一个点，不包括相同的第一个
                        add_theta=[np.linspace(theta_init[idx[i]-1],theta_init[idx[i]],add_number[i],endpoint=False)[1:] for i in range(np.shape(idx)[0])]
                    if 1:#多区间多点采样但精度设置不同
                        idx=np.where(error_hist>epsilon/np.sqrt(sample_n))[0]#不满足要求的点
                        #print(idx)
                        add_number=np.ceil((error_hist[idx]/epsilon*np.sqrt(sample_n))**0.2).astype(int)+1#至少要插入一个点，不包括相同的第一个
                        add_theta=[np.linspace(theta_init[idx[i]-1],theta_init[idx[i]],add_number[i],endpoint=False,dtype=np.float128)[1:] for i in range(np.shape(idx)[0])]
                    idx = np.repeat(idx, add_number-1) # create an index array with the same length as add_item
                    add_theta = np.concatenate(add_theta) # concatenate the list of arrays into a 1-D array
                    add_zeta_l=self.get_zeta_l(trajectory_l[i],add_theta).astype(np.complex128)
                    add_coff=self.get_poly_coff(add_zeta_l)
                    solution.add_points(idx,add_zeta_l,add_coff,add_theta)
                    sample_n=solution.sample_n
                    theta_init=solution.theta
                    error_hist=np.zeros_like(theta_init)
                    #solution.roots_print()
                    '''try:
                        test=1
                        print(solution.zeta_l[4509])
                        print(solution.theta[4509])
                        print(solution.roots[4509])
                        print(solution.parity[4509])
                        print(solution.coff[4509])
                        temp=np.roots(solution.coff[4513])
                        print(temp)
                        print(solution.verify(solution.zeta_l[4513],temp))
                        de_conjzeta_z1=self.m1/(np.conj(temp)-self.s)**2+self.m2/np.conj(temp)**2
                        print((1-(de_conjzeta_z1)*np.conj(de_conjzeta_z1)))
                    except IndexError:
                        test=0
                        pass'''
                try:
                    curve,theta,sol_num,parity_map=self.image_match(solution)
                except IndexError:
                    print(f'idx{i} occured indexerror please check')
                    quit()
                for k in range(len(curve)):
                    cur=curve[k]
                    theta_map_k=theta[k]
                    parity_k=parity_map[k]
                    mag_k=1/2*np.sum((cur.imag[0:-1]+cur.imag[1:])*(cur.real[0:-1]-cur.real[1:]))
                    mag+=mag_k*parity_k[0]
                    Error=Error_estimator(self.q,self.s,self.rho,cur,theta_map_k,theta_init,sol_num[k],parity_k)
                    error_k,parab=Error.error_sum()
                    error_hist+=error_k
                    mag+=parab
                    idx=np.where(error_hist>epsilon/np.sqrt(sample_n))[0]
                    if (k==1) :
                        plt.plot(cur.real,cur.imag,color='b')
                        plt.scatter(cur.real[idx],cur.imag[idx],color='r')
                        plt.show()
                error_tot=np.sum(error_hist)
                #print('error=',np.max(error_hist))
            add_list+=[sample_n]
            mag=mag/(np.pi*self.rho**2)
            mag_curve+=[mag]
            image_contour_all+=[curve]
        #np.savetxt('result/多区间多点采样tol设置为每个间隔的.txt',np.array(add_list),delimiter=',',fmt='%d')
            #print('idx =',i)
            #print('sample number =',sample_n)
        self.image_contour_all=image_contour_all
        return np.array(mag_curve)
    def draw_anim(self,fig,axis):#given  a series of roots return picture
        ims=[]
        theta=np.linspace(0,2*np.pi,100)
        trajectory_n=self.trajectory_n
        trajectory_l=self.trajectory_l
        curve=self.image_contour_all
        for i in range(trajectory_n):
            zeta=self.to_centroid(self.get_zeta_l(trajectory_l[i],theta))
            img_root=[]
            img2,=axis.plot(zeta.real,zeta.imag,color='r',label=str(i))
            ttl = plt.text(0.5, 1.01, i, horizontalalignment='center', verticalalignment='bottom', transform=axis.transAxes)
            for k in range(len(curve[i])):
                img1,=axis.plot(self.to_centroid(curve[i][k]).real,self.to_centroid(curve[i][k]).imag)
                img_root+=[img1]
            ims.append(img_root+[img2]+[ttl])
        ani=animation.ArtistAnimation(fig,ims,interval=100,repeat_delay=1000)
        writervideo = animation.FFMpegWriter(fps=30) 
        ani.save('picture/animation.mp4',writer=writervideo)
class Solution(object):
    def __init__(self,q,s,zeta_l,coff,theta):
        self.theta=theta
        self.q=q;self.s=s;self.m1=1/(1+q);self.m2=q/(1+q)
        self.zeta_l=zeta_l
        self.coff=coff
        self.sample_n=np.shape(zeta_l)[0]
        roots,parity=self.get_real_roots(coff,zeta_l)
        self.roots,self.parity=self.get_sorted_roots(self.sample_n,roots,parity)
        self.find_create_points()
    def add_points(self,idx,add_zeta,add_coff,add_theta):
        self.sample_n+=np.size(idx)
        self.theta=np.insert(self.theta,idx,add_theta)
        self.zeta_l=np.insert(self.zeta_l,idx,add_zeta)
        self.coff=np.insert(self.coff,idx,add_coff,axis=0)
        add_roots,add_parity=self.get_real_roots(add_coff,add_zeta)
        self.roots,self.parity=self.get_sorted_roots(self.sample_n,np.insert(self.roots,idx,add_roots,axis=0),np.insert(self.parity,idx,add_parity,axis=0))
        self.find_create_points()
    def get_roots(self,sample_n,coff,zeta_l):
        roots=np.empty((sample_n,5),dtype=complex)
        for k in range(sample_n):
            roots[k,:]=np.roots(coff[k,:])
        parity=self.get_parity(roots)
        error=self.verify(np.stack((zeta_l,zeta_l,zeta_l,zeta_l,zeta_l),axis=1),roots)
        cond=np.abs(error)>1e-6
        parity_sum=np.nansum(parity[~cond])
        return roots,cond,parity,parity_sum,error
    def get_real_roots(self,coff,zeta_l):
        sample_n=np.shape(zeta_l)[0]
        roots,cond,parity,parity_sum,error=self.get_roots(sample_n,coff,zeta_l)
        real_roots=np.where(cond,np.nan+np.nan*1j,roots)
        real_parity=np.where(cond,np.nan,parity)
        parity_sum=np.nansum(real_parity,axis=1)
        nan_num=cond.sum(axis=1)
        '''idx_normal=np.where(~((parity_sum==-1)&
                              ((nan_num==2)|(nan_num==0))))[0]#正确的根的索引'''
        idx_parity_wrong=np.where((nan_num==0)&
                                  (parity_sum!=-1))[0]#parity计算出现错误的根的索引
        ##对于parity计算错误的点，分为fifth principal left center right，其中left center right 的parity为-1，1，-1
        if np.size(idx_parity_wrong)!=0:
            for i in idx_parity_wrong:
                temp=real_roots[i]
                prin_root=temp[np.sign(temp.imag)==np.sign(zeta_l.imag[i])][0]
                prin_root=np.append(prin_root,temp[np.argmax(self.get_parity_error(temp))])
                other=np.setdiff1d(temp,prin_root)
                x_sort=np.argsort(other.real)
                parity[i][(temp==other[x_sort[0]])|(temp==other[x_sort[-1]])]=-1
                parity[i][(temp==other[x_sort[1]])]=1
        ####计算verify,如果parity出现错误或者nan个数错误，则重新规定error最大的为nan
        idx_verify_wrong=np.where(((nan_num==2)&(parity_sum!=-1))
                                  |((nan_num!=0)&(nan_num!=2)))[0]#verify出现错误的根的索引
        if np.size(idx_verify_wrong)!=0:
            sorted=np.argsort(error[idx_verify_wrong],axis=1)
            cond[idx_verify_wrong]=np.array([error[i,:]==error[i,sorted[-1]]|(error[i,:]==error[i,sorted[-2]])] 
                                            for i in range(np.size(idx_verify_wrong)))
        ###计算得到最终的
        real_roots=np.where(cond,np.nan+np.nan*1j,roots)
        real_parity=np.where(cond,np.nan,parity)
        return real_roots,real_parity
    def find_create_points(self):
        cond=np.isnan(self.roots)
        Is_create=np.zeros_like(self.roots,dtype=int)
        idx_x,idx_y=np.where(np.diff(cond,axis=0))
        idx_x+=1
        for x,y in zip(idx_x,idx_y):
            if ~cond[x,y]:#如果这个不是nan
                Is_create[x,y]=1#这个是destruction
            elif (cond[x,y])&(Is_create[x-1,y]!=1):#如果这个不是
                Is_create[x-1,y]=-1
            else:
                Is_create[x-1,y]-=1
        self.Is_create=Is_create
    def get_sorted_roots(self,sample_n,roots,parity):
        for k in range(sample_n):
            if k!=0:
                root_i_re_1=roots[k-1,:]
                parity_i_re_1=parity[k-1,:]
            root_i=roots[k,:]
            parity_i=parity[k,:]
            if k==0:
                idx=np.array([0,1,2,3,4])
            else:
                idx=self.find_nearest(root_i_re_1,parity_i_re_1,root_i,parity_i)
            roots[k,:]=root_i[idx]
            parity[k,:]=parity_i[idx]
        return roots,parity
    def find_nearest(self,array1, parity1, array2, parity2):
        array2=np.copy(array2)
        array2_c=np.copy(array2)
        array1_sorted=np.concatenate((np.sort(array1[parity1==1]),np.sort(array1[parity1==-1])))
        array2_sorted=np.concatenate((np.sort(array2[parity2==1]),np.sort(array2[parity2==-1])))
        leng1=np.shape(array1_sorted)[0]
        leng2=np.shape(array2_sorted)[0]
        if (leng1==5) & (leng2==5):
            mapping=dict(zip(array1_sorted,array2_sorted))
            array2=np.array([mapping[i] for i in array1])
        elif (leng1==3) & (leng2==3):
            mapping=dict(zip(array1_sorted,array2_sorted))
            for i in range(5):
                try:
                    array2[i]=mapping[array1[i]]
                except KeyError:
                    array2[i]=np.nan+1j*np.nan
        elif (leng1==3) & (leng2==5):#对应1，-1，-1与1，1，-1，-1，-1
            temp=np.zeros_like(array1[0:3])
            pos_idx=np.argmin(np.abs(array2_sorted[0:2]-array1_sorted[0]))#0,1两个parity为正的值
            temp[0]=array2_sorted[0:2][pos_idx]
            neg_idx_1=np.argmin(np.abs(array2_sorted[2:]-array1_sorted[1]))+2#2，3，4共三个parity为负的值，其中只能与2，3作比较
            temp[1]=array2_sorted[neg_idx_1]
            array2_sorted[neg_idx_1]=np.nan
            neg_idx_2=np.nanargmin(np.abs(array2_sorted[2:]-array1_sorted[2]))+2
            temp[2]=array2_sorted[neg_idx_2]
            unused=np.setdiff1d(array2,temp,True)
            mapping=dict(zip(array1_sorted,temp))
            k=0
            for i in range(5):
                try:
                    array2[i]=mapping[array1[i]]
                except KeyError:
                    array2[i]=unused[k]
                    k+=1
        elif (leng1==5) & (leng2==3):#对应1，1，-1，-1，-1与1，-1，-1
            temp=np.zeros_like(array1)
            temp[:]=np.nan+np.nan*1j
            pos_idx=np.argmin(np.abs(array1_sorted[0:2]-array2_sorted[0]))
            temp[pos_idx]=array2_sorted[0]
            neg_idx_1=np.argmin(np.abs(array1_sorted[2:]-array2_sorted[1]))+2
            temp[neg_idx_1]=array2_sorted[1]
            neg_idx_2=np.argmin(np.abs(array1_sorted[2:]-array2_sorted[2]))+2
            temp[neg_idx_2]=array2_sorted[2]
            mapping=dict(zip(array1_sorted,temp))
            array2=np.array([mapping[i] for i in array1])
        else :
            print('solution is wrong')
            quit()
        sort_indices = np.argsort(array2_c)
        indices = sort_indices[np.searchsorted(array2_c[sort_indices], array2)]
        return indices
    def verify(self,zeta_l,z_l):#verify whether the root is right
        return  z_l-self.m1/(np.conj(z_l)-self.s)-self.m2/np.conj(z_l)-zeta_l
    def get_parity(self,z):#get the parity of roots
        de_conjzeta_z1=self.m1/(np.conj(z)-self.s)**2+self.m2/np.conj(z)**2
        return np.sign((1-np.abs(de_conjzeta_z1)**2))
    def get_parity_error(self,z):
        de_conjzeta_z1=self.m1/(np.conj(z)-self.s)**2+self.m2/np.conj(z)**2
        return np.abs((1-np.abs(de_conjzeta_z1)**2))
    def root_polish(self,coff,roots,epsilon):
        p=np.poly1d(coff)
        derp=np.polyder(coff)
        for i in range(np.shape(roots)[0]):
            x_0=roots[i]
            temp=p(x_0)
            while p(x_0)>epsilon:
                if derp(x_0)<1e-14:
                    break
                x=x_0-p(x_0)/derp(x_0)
                x_0=x
            roots[i]=x_0
        return roots
    def roots_print(self):
        np.savetxt('result/roots.txt',self.roots,delimiter=',',fmt='%.4f')
        np.savetxt('result/parity.txt',self.parity,delimiter=',',fmt='%.0f')
        np.savetxt('result/create.txt',self.Is_create,delimiter=',',fmt='%.0f')
        np.savetxt('result/roots_diff.txt',np.abs(self.roots[1:]-self.roots[0:-1]),delimiter=',')
        np.savetxt('result/roots_verify.txt',self.verify(np.array([self.zeta_l,self.zeta_l,self.zeta_l,self.zeta_l,self.zeta_l]).T,self.roots),delimiter=',')
class Error_estimator(object):
    def __init__(self,q,s,rho,matched_image_l,theta_map,theta_init,sol_num,parity_map):
        self.q=q;self.s=s;self.rho=rho;self.cur_par=parity_map[0]
        zeta_l=matched_image_l;self.zeta_l=zeta_l
        theta=np.unwrap(theta_map);self.theta=theta;self.sol_num=sol_num#length=n
        self.theta_init=theta_init
        self.delta_theta=np.diff(theta)
        zeta_conj=np.conj(self.zeta_l)
        parZetaConZ=1/(1+q)*(1/(zeta_conj-s)**2+q/zeta_conj**2);self.parity=parity_map
        #par2ZetaConZ=-2/(1+q)*(1/(zeta_conj-s)**3+q/(zeta_conj)**3)
        par2ConZetaZ=-2/(1+q)*(1/(zeta_l-s)**3+q/(zeta_l)**3)
        de_zeta=1j*self.rho*np.exp(1j*theta)
        #de2_zeta=-self.rho*np.exp(1j*theta)
        detJ=1-np.abs(parZetaConZ)**2
        de_z=(de_zeta-parZetaConZ*np.conj(de_zeta))/detJ
        #de2_z=(de2_zeta-par2ZetaConZ*(np.conj(de_z)**2)-parZetaConZ*(np.conj(de2_zeta)-par2ConZetaZ*(de_z)**2))/detJ
        deXProde2X=(self.rho**2+np.imag(de_z**2*de_zeta*par2ConZetaZ))/detJ
        self.product=deXProde2X
        self.de_z=de_z
    def dot_product(self,a,b):
        return np.real(a)*np.real(b)+np.imag(a)*np.imag(b)
    def error_ordinary(self):
        deXProde2X=self.product
        delta_theta=self.delta_theta
        zeta_l=self.zeta_l
        e1=np.abs(1/48*np.abs(np.abs(deXProde2X[0:-1]-np.abs(deXProde2X[1:])))*delta_theta**3)
        dAp_1=1/24*((deXProde2X[0:-1]+deXProde2X[1:]))*delta_theta
        dAp=dAp_1*delta_theta**2
        delta_theta_wave=np.abs(zeta_l[0:-1]-zeta_l[1:])**2/np.abs(self.dot_product(self.de_z[0:-1],self.de_z[1:]))
        e2=3/2*np.abs(dAp_1*(delta_theta_wave-delta_theta**2))
        e3=1/10*np.abs(dAp)*delta_theta**2
        e_tot=(e1+e2+e3)/(np.pi*self.rho**2)
        return e_tot,self.cur_par*np.sum(dAp)#抛物线近似的补偿项
    def error_critial(self,critial_points):
        zeta_l=self.zeta_l
        de_z=self.de_z
        deXProde2X=self.product
        parity=self.parity
        pos_idx=critial_points;zeta_pos=zeta_l[pos_idx]
        neg_idx=critial_points+1;zeta_neg=zeta_l[neg_idx]
        theta_wave=np.abs(zeta_pos-zeta_neg)/np.sqrt(np.abs(self.dot_product(de_z[pos_idx],de_z[neg_idx])))
        ce1=1/48*np.abs(deXProde2X[pos_idx]+deXProde2X[neg_idx])*theta_wave**3
        Is_create=self.sol_num[pos_idx-(np.abs(self.sol_num[pos_idx])).astype(int)+1]#1 for ture -1 for false
        ce2=3/2*np.abs(self.dot_product(zeta_pos-zeta_neg,de_z[pos_idx]-de_z[neg_idx])-Is_create*2*np.abs(zeta_pos-zeta_neg)*np.sqrt(np.abs(self.dot_product(de_z[pos_idx],de_z[neg_idx]))))*theta_wave
        dAcP=parity[pos_idx]*1/24*(deXProde2X[pos_idx]-deXProde2X[neg_idx])*theta_wave**3
        ce3=1/10*np.abs(dAcP)*theta_wave**2
        ce_tot=(ce1+ce2+ce3)/(np.pi*self.rho**2)
        return ce_tot,np.sum(dAcP),Is_create#critial 附近的抛物线近似'''
    def error_sum(self):
        theta_init=self.theta_init
        e_ord,parab=self.error_ordinary()
        pos=np.argmax(e_ord)
        interval_theta=((self.theta[0:-1]+self.theta[1:])/2)#error 对应的区间的中心的theta值
        '''print(self.theta[pos]%(2*np.pi))
        print(self.theta[pos+1]%(2*np.pi))
        print((self.theta[pos]%(2*np.pi)+self.theta[pos+1]%(2*np.pi))/2)
        print(interval_theta[pos]%(2*np.pi))'''
        critial_points=np.nonzero(np.diff(self.parity))[0]
        if  np.shape(critial_points)[0]!=0:
            e_crit,dacp,Is_create=self.error_critial(critial_points)
            e_ord[critial_points]=e_crit
            interval_theta[critial_points]-=0.5*Is_create*np.min(np.abs(self.delta_theta[self.delta_theta!=0]))#如果error出现在creat则theta减小，缶则theta增加
            parab+=dacp
        error_map=np.zeros_like(theta_init)#error 按照theta 排序
        indices = np.searchsorted(theta_init, interval_theta%(2*np.pi))
        np.add.at(error_map,indices,e_ord)
        #print(theta_init[np.argmax(error_map)])
        return error_map,parab
if __name__=='__main__':
    if 0:
        b_map=np.linspace(-0.08,0.04,1200)
        b=b_map[797]
        t_0=2452848.06;t_E=61.5
        q=1e-4;alphadeg=90;s=1.0;rho=1e-3
        trajectory_n=300
        alpha=alphadeg*2*np.pi/360
        times=np.linspace(t_0-0.015*t_E,t_0+0.015*t_E,trajectory_n)
        model_uniform=model({'t_0': t_0, 'u_0': b, 't_E': t_E,
                            'rho': rho, 'q': q, 's': s, 'alpha_deg': alphadeg,'times':times})
        tra=model_uniform.trajectory_l[159]
        s=model_uniform.s
        m1=model_uniform.m1
        m2=model_uniform.m2
        theta_init=np.linspace(0,2*np.pi,10000)
        zeta=model_uniform.get_zeta_l(tra,theta_init)
        i=4513
        coff=model_uniform.get_poly_coff(zeta)[i]
        zeta=zeta[i]
        roots_all=np.roots(coff)
        print(np.sum(model_uniform.parity(roots_all)))
        roots_polished=model_uniform.root_polish(coff,roots_all,1e-10)
        print(model_uniform.verify(zeta,roots_all))
    if 1:
        a = np.array([5,4,3,2,1])
        b = np.array([1,2,3,4,5])
        # Get the indices of b in a using numpy.searchsorted()
        sort_indices = np.argsort(a)
        indices = sort_indices[np.searchsorted(a[sort_indices], b)]
        print(indices)



